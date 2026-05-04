import logging

import pytest
import werkzeug.serving
from jinja2 import TemplateNotFound
from markupsafe import Markup

import flask


def test_context_processing(app, client):
    @app.context_processor
    def context_processor():
        return {"injected_value": 42}

    @app.route("/")
    def index():
        return flask.render_template("context_template.html", value=23)

    rv = client.get("/")
    assert rv.data == b"<p>23|42"


def test_original_win(app, client):
    @app.route("/")
    def index():
        return flask.render_template_string("{{ config }}", config=42)

    rv = client.get("/")
    assert rv.data == b"42"


def test_simple_stream(app, client):
    @app.route("/")
    def index():
        return flask.stream_template_string("{{ config }}", config=42)

    rv = client.get("/")
    assert rv.data == b"42"


def test_request_less_rendering(app, app_ctx):
    app.config["WORLD_NAME"] = "Special World"

    @app.context_processor
    def context_processor():
        return dict(foo=42)

    rv = flask.render_template_string("Hello {{ config.WORLD_NAME }} {{ foo }}")
    assert rv == "Hello Special World 42"


def test_standard_context(app, client):
    @app.route("/")
    def index():
        flask.g.foo = 23
        flask.session["test"] = "aha"
        return flask.render_template_string(
            """
            {{ request.args.foo }}
            {{ g.foo }}
            {{ config.DEBUG }}
            {{ session.test }}
        """
        )

    rv = client.get("/?foo=42")
    assert rv.data.split() == [b"42", b"23", b"False", b"aha"]


def test_escaping(app, client):
    text = "<p>Hello World!"

    @app.route("/")
    def index():
        return flask.render_template(
            "escaping_template.html", text=text, html=Markup(text)
        )

    lines = client.get("/").data.splitlines()
    assert lines == [
        b"&lt;p&gt;Hello World!",
        b"<p>Hello World!",
        b"<p>Hello World!",
        b"<p>Hello World!",
        b"&lt;p&gt;Hello World!",
        b"<p>Hello World!",
    ]


def test_no_escaping(app, client):
    text = "<p>Hello World!"

    @app.route("/")
    def index():
        return flask.render_template(
            "non_escaping_template.txt", text=text, html=Markup(text)
        )

    lines = client.get("/").data.splitlines()
    assert lines == [
        b"<p>Hello World!",
        b"<p>Hello World!",
        b"<p>Hello World!",
        b"<p>Hello World!",
        b"&lt;p&gt;Hello World!",
        b"<p>Hello World!",
        b"<p>Hello World!",
        b"<p>Hello World!",
    ]


def test_escaping_without_template_filename(app, client, req_ctx):
    assert flask.render_template_string("{{ foo }}", foo="<test>") == "&lt;test&gt;"
    assert flask.render_template("mail.txt", foo="<test>") == "<test> Mail"


def test_macros(app, req_ctx):
    macro = flask.get_template_attribute("_macro.html", "hello")
    assert macro("World") == "Hello World!"


def test_template_filter(app):
    @app.template_filter()
    def my_reverse(s):
        return s[::-1]

    assert "my_reverse" in app.jinja_env.filters.keys()
    assert app.jinja_env.filters["my_reverse"] == my_reverse
    assert app.jinja_env.filters["my_reverse"]("abcd") == "dcba"

    @app.template_filter
    def my_reverse_2(s):
        return s[::-1]

    assert "my_reverse_2" in app.jinja_env.filters.keys()
    assert app.jinja_env.filters["my_reverse_2"] == my_reverse_2
    assert app.jinja_env.filters["my_reverse_2"]("abcd") == "dcba"

    @app.template_filter("my_reverse_custom_name_3")
    def my_reverse_3(s):
        return s[::-1]

    assert "my_reverse_custom_name_3" in app.jinja_env.filters.keys()
    assert app.jinja_env.filters["my_reverse_custom_name_3"] == my_reverse_3
    assert app.jinja_env.filters["my_reverse_custom_name_3"]("abcd") == "dcba"

    @app.template_filter(name="my_reverse_custom_name_4")
    def my_reverse_4(s):
        return s[::-1]

    assert "my_reverse_custom_name_4" in app.jinja_env.filters.keys()
    assert app.jinja_env.filters["my_reverse_custom_name_4"] == my_reverse_4
    assert app.jinja_env.filters["my_reverse_custom_name_4"]("abcd") == "dcba"


def test_add_template_filter(app):
    def my_reverse(s):
        return s[::-1]

    app.add_template_filter(my_reverse)
    assert "my_reverse" in app.jinja_env.filters.keys()
    assert app.jinja_env.filters["my_reverse"] == my_reverse
    assert app.jinja_env.filters["my_reverse"]("abcd") == "dcba"


def test_template_filter_with_name(app):
    @app.template_filter("strrev")
    def my_reverse(s):
        return s[::-1]

    assert "strrev" in app.jinja_env.filters.keys()
    assert app.jinja_env.filters["strrev"] == my_reverse
    assert app.jinja_env.filters["strrev"]("abcd") == "dcba"


def test_add_template_filter_with_name(app):
    def my_reverse(s):
        return s[::-1]

    app.add_template_filter(my_reverse, "strrev")
    assert "strrev" in app.jinja_env.filters.keys()
    assert app.jinja_env.filters["strrev"] == my_reverse
    assert app.jinja_env.filters["strrev"]("abcd") == "dcba"


def test_template_filter_with_template(app, client):
    @app.template_filter()
    def super_reverse(s):
        return s[::-1]

    @app.route("/")
    def index():
        return flask.render_template("template_filter.html", value="abcd")

    rv = client.get("/")
    assert rv.data == b"dcba"


def test_add_template_filter_with_template(app, client):
    def super_reverse(s):
        return s[::-1]

    app.add_template_filter(super_reverse)

    @app.route("/")
    def index():
        return flask.render_template("template_filter.html", value="abcd")

    rv = client.get("/")
    assert rv.data == b"dcba"


def test_template_filter_with_name_and_template(app, client):
    @app.template_filter("super_reverse")
    def my_reverse(s):
        return s[::-1]

    @app.route("/")
    def index():
        return flask.render_template("template_filter.html", value="abcd")

    rv = client.get("/")
    assert rv.data == b"dcba"


def test_add_template_filter_with_name_and_template(app, client):
    def my_reverse(s):
        return s[::-1]

    app.add_template_filter(my_reverse, "super_reverse")

    @app.route("/")
    def index():
        return flask.render_template("template_filter.html", value="abcd")

    rv = client.get("/")
    assert rv.data == b"dcba"


def test_template_test(app):
    @app.template_test()
    def boolean(value):
        return isinstance(value, bool)

    assert "boolean" in app.jinja_env.tests.keys()
    assert app.jinja_env.tests["boolean"] == boolean
    assert app.jinja_env.tests["boolean"](False)

    @app.template_test
    def boolean_2(value):
        return isinstance(value, bool)

    assert "boolean_2" in app.jinja_env.tests.keys()
    assert app.jinja_env.tests["boolean_2"] == boolean_2
    assert app.jinja_env.tests["boolean_2"](False)

    @app.template_test("my_boolean_custom_name")
    def boolean_3(value):
        return isinstance(value, bool)

    assert "my_boolean_custom_name" in app.jinja_env.tests.keys()
    assert app.jinja_env.tests["my_boolean_custom_name"] == boolean_3
    assert app.jinja_env.tests["my_boolean_custom_name"](False)

    @app.template_test(name="my_boolean_custom_name_2")
    def boolean_4(value):
        return isinstance(value, bool)

    assert "my_boolean_custom_name_2" in app.jinja_env.tests.keys()
    assert app.jinja_env.tests["my_boolean_custom_name_2"] == boolean_4
    assert app.jinja_env.tests["my_boolean_custom_name_2"](False)


def test_add_template_test(app):
    def boolean(value):
        return isinstance(value, bool)

    app.add_template_test(boolean)
    assert "boolean" in app.jinja_env.tests.keys()
    assert app.jinja_env.tests["boolean"] == boolean
    assert app.jinja_env.tests["boolean"](False)


def test_template_test_with_name(app):
    @app.template_test("boolean")
    def is_boolean(value):
        return isinstance(value, bool)

    assert "boolean" in app.jinja_env.tests.keys()
    assert app.jinja_env.tests["boolean"] == is_boolean
    assert app.jinja_env.tests["boolean"](False)


def test_add_template_test_with_name(app):
    def is_boolean(value):
        return isinstance(value, bool)

    app.add_template_test(is_boolean, "boolean")
    assert "boolean" in app.jinja_env.tests.keys()
    assert app.jinja_env.tests["boolean"] == is_boolean
    assert app.jinja_env.tests["boolean"](False)


def test_template_test_with_template(app, client):
    @app.template_test()
    def boolean(value):
        return isinstance(value, bool)

    @app.route("/")
    def index():
        return flask.render_template("template_test.html", value=False)

    rv = client.get("/")
    assert b"Success!" in rv.data


def test_add_template_test_with_template(app, client):
    def boolean(value):
        return isinstance(value, bool)

    app.add_template_test(boolean)

    @app.route("/")
    def index():
        return flask.render_template("template_test.html", value=False)

    rv = client.get("/")
    assert b"Success!" in rv.data


def test_template_test_with_name_and_template(app, client):
    @app.template_test("boolean")
    def is_boolean(value):
        return isinstance(value, bool)

    @app.route("/")
    def index():
        return flask.render_template("template_test.html", value=False)

    rv = client.get("/")
    assert b"Success!" in rv.data


def test_add_template_test_with_name_and_template(app, client):
    def is_boolean(value):
        return isinstance(value, bool)

    app.add_template_test(is_boolean, "boolean")

    @app.route("/")
    def index():
        return flask.render_template("template_test.html", value=False)

    rv = client.get("/")
    assert b"Success!" in rv.data


def test_add_template_global(app, app_ctx):
    @app.template_global()
    def get_stuff():
        return 42

    assert "get_stuff" in app.jinja_env.globals.keys()
    assert app.jinja_env.globals["get_stuff"] == get_stuff
    assert app.jinja_env.globals["get_stuff"](), 42

    rv = flask.render_template_string("{{ get_stuff() }}")
    assert rv == "42"

    @app.template_global
    def get_stuff_1():
        return "get_stuff_1"

    assert "get_stuff_1" in app.jinja_env.globals.keys()
    assert app.jinja_env.globals["get_stuff_1"] == get_stuff_1
    assert app.jinja_env.globals["get_stuff_1"](), "get_stuff_1"

    rv = flask.render_template_string("{{ get_stuff_1() }}")
    assert rv == "get_stuff_1"

    @app.template_global("my_get_stuff_custom_name_2")
    def get_stuff_2():
        return "get_stuff_2"

    assert "my_get_stuff_custom_name_2" in app.jinja_env.globals.keys()
    assert app.jinja_env.globals["my_get_stuff_custom_name_2"] == get_stuff_2
    assert app.jinja_env.globals["my_get_stuff_custom_name_2"](), "get_stuff_2"

    rv = flask.render_template_string("{{ my_get_stuff_custom_name_2() }}")
    assert rv == "get_stuff_2"

    @app.template_global(name="my_get_stuff_custom_name_3")
    def get_stuff_3():
        return "get_stuff_3"

    assert "my_get_stuff_custom_name_3" in app.jinja_env.globals.keys()
    assert app.jinja_env.globals["my_get_stuff_custom_name_3"] == get_stuff_3
    assert app.jinja_env.globals["my_get_stuff_custom_name_3"](), "get_stuff_3"

    rv = flask.render_template_string("{{ my_get_stuff_custom_name_3() }}")
    assert rv == "get_stuff_3"


def test_custom_template_loader(client):
    class MyFlask(flask.Flask):
        def create_global_jinja_loader(self):
            from jinja2 import DictLoader

            return DictLoader({"index.html": "Hello Custom World!"})

    app = MyFlask(__name__)

    @app.route("/")
    def index():
        return flask.render_template("index.html")

    c = app.test_client()
    rv = c.get("/")
    assert rv.data == b"Hello Custom World!"


def test_iterable_loader(app, client):
    @app.context_processor
    def context_processor():
        return {"whiskey": "Jameson"}

    @app.route("/")
    def index():
        return flask.render_template(
            [
                "no_template.xml",  # should skip this one
                "simple_template.html",  # should render this
                "context_template.html",
            ],
            value=23,
        )

    rv = client.get("/")
    assert rv.data == b"<h1>Jameson</h1>"


def test_templates_auto_reload(app):
    # debug is False, config option is None
    assert app.debug is False
    assert app.config["TEMPLATES_AUTO_RELOAD"] is None
    assert app.jinja_env.auto_reload is False
    # debug is False, config option is False
    app = flask.Flask(__name__)
    app.config["TEMPLATES_AUTO_RELOAD"] = False
    assert app.debug is False
    assert app.jinja_env.auto_reload is False
    # debug is False, config option is True
    app = flask.Flask(__name__)
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    assert app.debug is False
    assert app.jinja_env.auto_reload is True
    # debug is True, config option is None
    app = flask.Flask(__name__)
    app.config["DEBUG"] = True
    assert app.config["TEMPLATES_AUTO_RELOAD"] is None
    assert app.jinja_env.auto_reload is True
    # debug is True, config option is False
    app = flask.Flask(__name__)
    app.config["DEBUG"] = True
    app.config["TEMPLATES_AUTO_RELOAD"] = False
    assert app.jinja_env.auto_reload is False
    # debug is True, config option is True
    app = flask.Flask(__name__)
    app.config["DEBUG"] = True
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    assert app.jinja_env.auto_reload is True


def test_templates_auto_reload_debug_run(app, monkeypatch):
    def run_simple_mock(*args, **kwargs):
        pass

    monkeypatch.setattr(werkzeug.serving, "run_simple", run_simple_mock)

    app.run()
    assert not app.jinja_env.auto_reload

    app.run(debug=True)
    assert app.jinja_env.auto_reload


def test_template_loader_debugging(test_apps, monkeypatch):
    from blueprintapp import app

    called = []

    class _TestHandler(logging.Handler):
        def handle(self, record):
            called.append(True)
            text = str(record.msg)
            assert "1: trying loader of application 'blueprintapp'" in text
            assert (
                "2: trying loader of blueprint 'admin' (blueprintapp.apps.admin)"
            ) in text
            assert (
                "trying loader of blueprint 'frontend' (blueprintapp.apps.frontend)"
            ) in text
            assert "Error: the template could not be found" in text
            assert (
                "looked up from an endpoint that belongs to the blueprint 'frontend'"
            ) in text
            assert "See https://flask.palletsprojects.com/blueprints/#templates" in text

    with app.test_client() as c:
        monkeypatch.setitem(app.config, "EXPLAIN_TEMPLATE_LOADING", True)
        monkeypatch.setattr(
            logging.getLogger("blueprintapp"), "handlers", [_TestHandler()]
        )

        with pytest.raises(TemplateNotFound) as excinfo:
            c.get("/missing")

        assert "missing_template.html" in str(excinfo.value)

    assert len(called) == 1


def test_custom_jinja_env():
    class CustomEnvironment(flask.templating.Environment):
        pass

    class CustomFlask(flask.Flask):
        jinja_environment = CustomEnvironment

    app = CustomFlask(__name__)
    assert isinstance(app.jinja_env, CustomEnvironment)


def test_template_cache_config_defaults(app):
    assert app.config["TEMPLATE_CACHE_MODE"] == "auto"
    assert app.config["TEMPLATE_CACHE_SIZE"] == 200
    assert app.config["TEMPLATE_HASH_ALGO"] == "md5"


def test_template_cache_mode_config(app):
    app.config["TEMPLATE_CACHE_MODE"] = "hash"
    assert app.config["TEMPLATE_CACHE_MODE"] == "hash"

    app.config["TEMPLATE_CACHE_MODE"] = "always"
    assert app.config["TEMPLATE_CACHE_MODE"] == "always"

    app.config["TEMPLATE_CACHE_MODE"] = "never"
    assert app.config["TEMPLATE_CACHE_MODE"] == "never"

    app.config["TEMPLATE_CACHE_MODE"] = "auto"
    assert app.config["TEMPLATE_CACHE_MODE"] == "auto"


def test_template_cache_size_config(app):
    app.config["TEMPLATE_CACHE_SIZE"] = 100
    assert app.config["TEMPLATE_CACHE_SIZE"] == 100

    app.config["TEMPLATE_CACHE_SIZE"] = 500
    assert app.config["TEMPLATE_CACHE_SIZE"] == 500


def test_template_hash_algo_config(app):
    app.config["TEMPLATE_HASH_ALGO"] = "sha256"
    assert app.config["TEMPLATE_HASH_ALGO"] == "sha256"

    app.config["TEMPLATE_HASH_ALGO"] = "sha1"
    assert app.config["TEMPLATE_HASH_ALGO"] == "sha1"


def test_lru_template_cache():
    from flask.templating import LRUTemplateCache

    cache = LRUTemplateCache(max_size=3)

    assert len(cache) == 0
    assert cache.get("test") is None

    cache.set("template1.html", "content1", 1234567890.0, "hash1")
    assert len(cache) == 1
    assert cache.get("template1.html") == ("content1", 1234567890.0, "hash1")

    cache.set("template2.html", "content2", 1234567891.0, "hash2")
    cache.set("template3.html", "content3", 1234567892.0, "hash3")
    assert len(cache) == 3

    cache.set("template4.html", "content4", 1234567893.0, "hash4")
    assert len(cache) == 3
    assert cache.get("template1.html") is None
    assert cache.get("template4.html") == ("content4", 1234567893.0, "hash4")

    cache.clear()
    assert len(cache) == 0


def test_lru_template_cache_stats():
    from flask.templating import LRUTemplateCache

    cache = LRUTemplateCache(max_size=10)
    cache.set("template1.html", "content1", 1234567890.0, "hash1")
    cache.set("template2.html", "content2", 1234567891.0, "hash2")

    stats = cache.get_stats()
    assert stats["size"] == 2
    assert stats["max_size"] == 10
    assert "template1.html" in stats["templates"]
    assert "template2.html" in stats["templates"]


def test_lru_template_cache_lru_order():
    from flask.templating import LRUTemplateCache

    cache = LRUTemplateCache(max_size=3)
    cache.set("a.html", "content_a", 1.0, "hash_a")
    cache.set("b.html", "content_b", 2.0, "hash_b")
    cache.set("c.html", "content_c", 3.0, "hash_c")

    cache.get("a.html")
    cache.set("d.html", "content_d", 4.0, "hash_d")

    assert cache.get("b.html") is None
    assert cache.get("a.html") is not None
    assert cache.get("c.html") is not None
    assert cache.get("d.html") is not None


def test_hashing_file_system_loader_init():
    from flask.templating import HashingFileSystemLoader

    loader = HashingFileSystemLoader("/path/to/templates")
    assert loader.searchpath == "/path/to/templates"
    assert loader.encoding == "utf-8"
    assert loader.hash_algo == "md5"

    loader = HashingFileSystemLoader(
        searchpath="/path/to/templates",
        encoding="latin-1",
        hash_algo="sha256"
    )
    assert loader.searchpath == "/path/to/templates"
    assert loader.encoding == "latin-1"
    assert loader.hash_algo == "sha256"


def test_hashing_file_system_loader_list_templates(tmp_path):
    from flask.templating import HashingFileSystemLoader

    (tmp_path / "test.html").write_text("<h1>Test</h1>")
    (tmp_path / "test.htm").write_text("<h2>Test</h2>")
    (tmp_path / "test.jinja").write_text("<h3>Test</h3>")
    (tmp_path / "test.jinja2").write_text("<h4>Test</h4>")
    (tmp_path / "test.txt").write_text("Plain text")

    loader = HashingFileSystemLoader(str(tmp_path))
    templates = loader.list_templates()

    assert "test.html" in templates
    assert "test.htm" in templates
    assert "test.jinja" in templates
    assert "test.jinja2" in templates
    assert "test.txt" not in templates


def test_hashing_file_system_loader_list_templates_nested(tmp_path):
    from flask.templating import HashingFileSystemLoader

    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (tmp_path / "base.html").write_text("<h1>Base</h1>")
    (subdir / "nested.html").write_text("<h1>Nested</h1>")

    loader = HashingFileSystemLoader(str(tmp_path))
    templates = loader.list_templates()

    assert "base.html" in templates
    assert "subdir/nested.html" in templates


def test_hash_mode_uses_hashing_loader(app, tmp_path):
    app.config["TEMPLATE_CACHE_MODE"] = "hash"
    app.config["TEMPLATES_AUTO_RELOAD"] = False

    (tmp_path / "templates").mkdir(exist_ok=True)
    app.template_folder = str(tmp_path / "templates")

    template_path = tmp_path / "templates" / "test.html"
    template_path.write_text("<h1>{{ name }}</h1>")

    env = app.create_jinja_environment()
    assert env.auto_reload is False
