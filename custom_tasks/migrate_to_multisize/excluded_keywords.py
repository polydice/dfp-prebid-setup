keywords = ['PC', 'Desktop', 'Sidebar_Bottom', 'Interstitial']


def is_excluded_order(order_name):
    keywords = [
        'PC',
        'Desktop',
        'Sidebar_Bottom',
        'Interstitial',
        'AMP'
    ]
    return any(word in order_name for word in keywords)
