# coding: utf-8
from ircbot import convert_message


def test_slack_to_irc():
    assert convert_message('hello') == 'hello'
    assert convert_message('유니코드') == '유니코드'
    assert convert_message('multi\r\nline') == 'multi  line'
    assert convert_message('A: <https://example.com/something/url/94446>') == 'A: https://example.com/something/url/94446'
    assert convert_message('B: <#C4NETGXXX|server-channel>') == 'B: #server-channel'
    assert convert_message('let x: Box&lt;T&gt; = ...') == 'let x: Box<T> = ...'
