import sublime, sublime_plugin
import html.parser
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

def print_content(content):
    semi_pretty = ''.join(content.split('<p>'))
    h = html.parser.HTMLParser()
    semi_pretty = h.unescape(semi_pretty)
    pretty_content = semi_pretty.replace('<i>', '_').replace('</i>','_')
    return pretty_content

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
        titles = [[item['title'], self._get_subtitle(item)] for i, item in enumerate(self.news_dict)]
        self.window.show_quick_panel(titles, on_select=self.handle)

    def handle(self, val):
        if val == -1:
            return
        article = self.news_dict[val]
        aview = self.window.new_file()
        config_view(aview, title=article['title'], theme=self.settings.get('theme'))
        aview.settings().set('article_id', article['id'])
        aview.settings().set('article_title', article['title'])
        thread = hackernews.ArticleExtract(article['url'])
        thread.start()
        self.handle_article_thread(thread, aview)

    def handle_article_thread(self, thread, view):
        if thread.result is None:
            sublime.status_message('Fetching %s' % thread.url)
            sublime.set_timeout(lambda: self.handle_article_thread(thread, view), 100)
            return
        elif thread.result is False:
            sublime.error_message(thread.err)
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

class ShowCommentsCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        article_id = self.view.settings().get('article_id', None)
        self.edit = edit
        if article_id is None:
            return
        settings = sublime.load_settings(SETTINGS_FILE)
        hackernews.config_proxy(settings.get('http_proxy'))
        thread = hackernews.CommentsFetcher(article_id)
        thread.start()
        cview = self.view.window().new_file()
        config_view(cview, title=self.view.settings().get('article_title', 'Comments'), 
            theme=settings.get('theme'))
        self.handle_comments_thread(thread, cview)

    def handle_comments_thread(self, thread, view):
        if thread.result is None:
            sublime.status_message('Fetching comments')
            sublime.set_timeout(lambda: self.handle_comments_thread(thread, view), 100)
            return
        elif thread.result is False:
            sublime.error_message(thread.err)
            return
        comments = thread.result
        _comments = comments['comments']
        view.run_command('print_comments', {'comments' : _comments})

class PrintCommentsCommand(sublime_plugin.TextCommand):

    def run(self, edit, comments):
        self._offset = 0
        self.edit = edit
        self.print_comments(comments)
        self.view.set_read_only(True)

    def print_comments(self, comments):
        if not comments:
            return
        for comment in comments:
            level = comment['level']
            tabbing = '\t'*level
            user = comment.get('user', 'User')
            content = print_content(comment['content'])
            self._offset += self.view.insert(self.edit, self._offset, tabbing + content + '\n')
            self._offset += self.view.insert(self.edit, self._offset, tabbing + '%s | %s\n\n' % (user, comment['time_ago']))
            self.print_comments(comment['comments'])



