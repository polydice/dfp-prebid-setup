def log(*msgs, type=None):
    def p(msg):
        print(msg, end=' ')

    placeholder = '  '
    if type == 'passed':
        placeholder += '✅' + placeholder
    elif type == 'warn':
        placeholder += '⚠️' + placeholder
    elif type == 'progress':
        placeholder += '🏃' + placeholder

    p(placeholder)
    for msg in msgs:
        p(msg)
    print()
