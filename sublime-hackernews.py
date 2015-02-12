import sublime, sublime_plugin
from .import hackernews

SETTINGS_FILE = 'sublime-hackernews.sublime-settings'
DEFAULT_THEME = 'Packages/Color Scheme - Default/Dawn.tmTheme'

def config_view(view, title='Hacker news', theme=DEFAULT_THEME):
    # Wait until the view loads
    while view.is_loading():
        pass

    view.set_name(title)
    view.set_scratch(True)
    view.settings().set('color_scheme', theme)

class HackerNewsCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.settings = sublime.load_settings(SETTINGS_FILE)
        hackernews.config_proxy(self.settings.get('http_proxy'))
        thread = hackernews.HackerNewsApiCall()
        thread.start()
        self.handle_thread(thread)
        return

    def handle_thread(self, thread):
        if thread.result is None:
            sublime.status_message('Fetching News')
            sublime.set_timeout(lambda: self.handle_thread(thread), 100)
            return
        elif thread.result is False:
            sublime.error_message(thread.err)
            return
        self.news_dict = thread.result
        print(self.news_dict)
        titles = [[item['title'], self._get_subtitle(item)] for i, item in enumerate(self.news_dict)]
        self.window.show_quick_panel(titles, on_select=self.handle)

    def handle(self, val):
        if val == -1:
            return
        article = self.news_dict[val]
        aview = self.window.new_file()
        config_view(aview, title=article['title'], theme=self.settings.get('theme'))
        thread = hackernews.ArticleExtract(article['url'])
        thread.start()
        self.handle_article_thread(thread, aview)

    def handle_article_thread(self, thread, view):
        if not thread.result:
            sublime.status_message('Fetching %s' % thread.url)
            sublime.set_timeout(lambda: self.handle_article_thread(thread, view), 100)
            return
        view.run_command('show_article', {'data' : thread.result})

    def _get_subtitle(self, item):
        subtitle = '%d comments' % item['comments_count']
        points = item['points']
        if points:
            subtitle += (' | %d points' % points)
        return subtitle

class ShowArticleCommand(sublime_plugin.TextCommand):
    def run(self, edit, data):
        sublime.status_message('Fetched')
        self.view.insert(edit, 0, data)
        self.view.set_read_only(True)
