from __future__ import annotations

import hashlib
import typing as t
from collections import OrderedDict
from functools import lru_cache

from jinja2 import BaseLoader
from jinja2 import Environment as BaseEnvironment
from jinja2 import Template
from jinja2 import TemplateNotFound

from .ctx import AppContext
from .globals import app_ctx
from .helpers import stream_with_context
from .signals import before_render_template
from .signals import template_rendered

if t.TYPE_CHECKING:  # pragma: no cover
    from .sansio.app import App
    from .sansio.scaffold import Scaffold


class LRUTemplateCache:
    """A size-limited LRU cache for Jinja2 templates."""

    def __init__(self, max_size: int = 200) -> None:
        self.max_size = max_size
        self._cache: OrderedDict[str, tuple[str, float, str]] = OrderedDict()

    def get(self, key: str) -> tuple[str, float, str] | None:
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def set(self, key: str, source: str, mtime: float, content_hash: str) -> None:
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = (source, mtime, content_hash)
        while len(self._cache) > self.max_size:
            self._cache.popitem(last=False)

    def clear(self) -> None:
        self._cache.clear()

    def __len__(self) -> int:
        return len(self._cache)

    def get_stats(self) -> dict[str, t.Any]:
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "templates": list(self._cache.keys()),
        }


class HashingFileSystemLoader(BaseLoader):
    """A Jinja2 file system loader that supports hash-based cache validation.

    This loader computes a hash of the template file content to determine
    if the cached version is still valid, rather than relying solely on mtime.
    """

    def __init__(
        self,
        searchpath: str | list[str],
        encoding: str = "utf-8",
        hash_algo: str = "md5",
    ) -> None:
        self.searchpath = searchpath
        self.encoding = encoding
        self.hash_algo = hash_algo

    def get_source(
        self, environment: BaseEnvironment, template: str
    ) -> tuple[str, str | None, t.Callable[[], bool] | None]:
        if isinstance(self.searchpath, str):
            searchpaths = [self.searchpath]
        else:
            searchpaths = self.searchpath

        for searchpath in searchpaths:
            try:
                from os.path import join
                from os.path import isfile
                import time

                filename = join(searchpath, template)
                if isfile(filename):
                    with open(filename, "r", encoding=self.encoding) as f:
                        source = f.read()

                    mtime = isfile(filename) and time.localtime(filename).st_mtime or 0
                    hash_func = getattr(hashlib, self.hash_algo)
                    content_hash = hash_func(source.encode(self.encoding)).hexdigest()

                    def check_uptodate(file_mtime: float = mtime, file_hash: str = content_hash) -> bool:
                        try:
                            import os
                            current_mtime = os.path.getmtime(filename)
                            if current_mtime != file_mtime:
                                with open(filename, "r", encoding=self.encoding) as f:
                                    current_source = f.read()
                                current_hash = hash_func(current_source.encode(self.encoding)).hexdigest()
                                return current_hash == file_hash
                            return True
                        except OSError:
                            return False

                    return source, filename, check_uptodate
            except (IOError, OSError):
                continue

        raise TemplateNotFound(template)

    def list_templates(self) -> list[str]:
        found = set()
        if isinstance(self.searchpath, str):
            searchpaths = [self.searchpath]
        else:
            searchpaths = self.searchpath

        for searchpath in searchpaths:
            try:
                from os import walk
                from os.path import join

                for dirpath, _, filenames in walk(searchpath):
                    for filename in filenames:
                        if filename.endswith((".html", ".htm", ".jinja", ".jinja2")):
                            template = join(dirpath, filename)
                            found.add(template[len(searchpath) + 1:].replace("\\", "/"))
            except (IOError, OSError):
                continue

        return sorted(found)


def _default_template_ctx_processor() -> dict[str, t.Any]:
    """Default template context processor.  Replaces the ``request`` and ``g``
    proxies with their concrete objects for faster access.
    """
    ctx = app_ctx._get_current_object()
    rv: dict[str, t.Any] = {"g": ctx.g}

    if ctx.has_request:
        rv["request"] = ctx.request
        # The session proxy cannot be replaced, accessing it gets
        # RequestContext.session, which sets session.accessed.

    return rv


class Environment(BaseEnvironment):
    """Works like a regular Jinja environment but has some additional
    knowledge of how Flask's blueprint works so that it can prepend the
    name of the blueprint to referenced templates if necessary.
    """

    def __init__(self, app: App, **options: t.Any) -> None:
        if "loader" not in options:
            options["loader"] = app.create_global_jinja_loader()
        BaseEnvironment.__init__(self, **options)
        self.app = app


class DispatchingJinjaLoader(BaseLoader):
    """A loader that looks for templates in the application and all
    the blueprint folders.
    """

    def __init__(self, app: App) -> None:
        self.app = app

    def get_source(
        self, environment: BaseEnvironment, template: str
    ) -> tuple[str, str | None, t.Callable[[], bool] | None]:
        if self.app.config["EXPLAIN_TEMPLATE_LOADING"]:
            return self._get_source_explained(environment, template)
        return self._get_source_fast(environment, template)

    def _get_source_explained(
        self, environment: BaseEnvironment, template: str
    ) -> tuple[str, str | None, t.Callable[[], bool] | None]:
        attempts = []
        rv: tuple[str, str | None, t.Callable[[], bool] | None] | None
        trv: None | (tuple[str, str | None, t.Callable[[], bool] | None]) = None

        for srcobj, loader in self._iter_loaders(template):
            try:
                rv = loader.get_source(environment, template)
                if trv is None:
                    trv = rv
            except TemplateNotFound:
                rv = None
            attempts.append((loader, srcobj, rv))

        from .debughelpers import explain_template_loading_attempts

        explain_template_loading_attempts(self.app, template, attempts)

        if trv is not None:
            return trv
        raise TemplateNotFound(template)

    def _get_source_fast(
        self, environment: BaseEnvironment, template: str
    ) -> tuple[str, str | None, t.Callable[[], bool] | None]:
        for _srcobj, loader in self._iter_loaders(template):
            try:
                return loader.get_source(environment, template)
            except TemplateNotFound:
                continue
        raise TemplateNotFound(template)

    def _iter_loaders(self, template: str) -> t.Iterator[tuple[Scaffold, BaseLoader]]:
        loader = self.app.jinja_loader
        if loader is not None:
            yield self.app, loader

        for blueprint in self.app.iter_blueprints():
            loader = blueprint.jinja_loader
            if loader is not None:
                yield blueprint, loader

    def list_templates(self) -> list[str]:
        result = set()
        loader = self.app.jinja_loader
        if loader is not None:
            result.update(loader.list_templates())

        for blueprint in self.app.iter_blueprints():
            loader = blueprint.jinja_loader
            if loader is not None:
                for template in loader.list_templates():
                    result.add(template)

        return list(result)


def _render(ctx: AppContext, template: Template, context: dict[str, t.Any]) -> str:
    app = ctx.app
    app.update_template_context(ctx, context)
    before_render_template.send(
        app, _async_wrapper=app.ensure_sync, template=template, context=context
    )
    rv = template.render(context)
    template_rendered.send(
        app, _async_wrapper=app.ensure_sync, template=template, context=context
    )
    return rv


def render_template(
    template_name_or_list: str | Template | list[str | Template],
    **context: t.Any,
) -> str:
    """Render a template by name with the given context.

    :param template_name_or_list: The name of the template to render. If
        a list is given, the first name to exist will be rendered.
    :param context: The variables to make available in the template.
    """
    ctx = app_ctx._get_current_object()
    template = ctx.app.jinja_env.get_or_select_template(template_name_or_list)
    return _render(ctx, template, context)


def render_template_string(source: str, **context: t.Any) -> str:
    """Render a template from the given source string with the given
    context.

    :param source: The source code of the template to render.
    :param context: The variables to make available in the template.
    """
    ctx = app_ctx._get_current_object()
    template = ctx.app.jinja_env.from_string(source)
    return _render(ctx, template, context)


def _stream(
    ctx: AppContext, template: Template, context: dict[str, t.Any]
) -> t.Iterator[str]:
    app = ctx.app
    app.update_template_context(ctx, context)
    before_render_template.send(
        app, _async_wrapper=app.ensure_sync, template=template, context=context
    )

    def generate() -> t.Iterator[str]:
        yield from template.generate(context)
        template_rendered.send(
            app, _async_wrapper=app.ensure_sync, template=template, context=context
        )

    return stream_with_context(generate())


def stream_template(
    template_name_or_list: str | Template | list[str | Template],
    **context: t.Any,
) -> t.Iterator[str]:
    """Render a template by name with the given context as a stream.
    This returns an iterator of strings, which can be used as a
    streaming response from a view.

    :param template_name_or_list: The name of the template to render. If
        a list is given, the first name to exist will be rendered.
    :param context: The variables to make available in the template.

    .. versionadded:: 2.2
    """
    ctx = app_ctx._get_current_object()
    template = ctx.app.jinja_env.get_or_select_template(template_name_or_list)
    return _stream(ctx, template, context)


def stream_template_string(source: str, **context: t.Any) -> t.Iterator[str]:
    """Render a template from the given source string with the given
    context as a stream. This returns an iterator of strings, which can
    be used as a streaming response from a view.

    :param source: The source code of the template to render.
    :param context: The variables to make available in the template.

    .. versionadded:: 2.2
    """
    ctx = app_ctx._get_current_object()
    template = ctx.app.jinja_env.from_string(source)
    return _stream(ctx, template, context)
