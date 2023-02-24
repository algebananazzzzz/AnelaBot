import nltk
from nltk.tokenize import word_tokenize
import nltk.tag
from nltk import RegexpTagger
import parsedatetime


cal = parsedatetime.Calendar()

patterns = {r'^(?:(?:31(\/|-|\.)(?:0?[13578]|1[02]))\1|(?:(?:29|30)(\/|-|\.)(?:0?[13-9]|1[0-2])\2))(?:(?:1[6-9]|[2-9]\d)?\d{2})$|^(?:29(\/|-|\.)0?2\3(?:(?:(?:1[6-9]|[2-9]\d)?(?:0[48]|[2468][048]|[13579][26])|(?:(?:16|[2468][048]|[3579][26])00))))$|^(?:0?[1-9]|1\d|2[0-8])(\/|-|\.)(?:(?:0?[1-9])|(?:1[0-2]))\4(?:(?:1[6-9]|[2-9]\d)?\d{2})$': 'DATE_DMY',
            r'^(?:(?:31(\/|-|\.)(?:0?[13578]|1[02]))\1|(?:(?:29|30)(\/|-|\.)(?:0?[13-9]|1[0-2])\2))(?:(?:1[6-9]|[2-9]\d)?\d{2})$|^(?:29(\/|-|\.)0?2\3(?:(?:(?:1[6-9]|[2-9]\d)?(?:0[48]|[2468][048]|[13579][26])|(?:(?:16|[2468][048]|[3579][26])00))))$|^(?:0?[1-9]|1\d|2[0-8])(\/|-|\.)(?:(?:0?[1-9])|(?:1[0-2]))$': 'DATE_DM',
            r'^(?:Jan|jan(?:uary)?|Feb|feb(?:ruary)?|Mar|mar(?:ch)?|Apr|apr(?:il)?|May|may|Jun|jun(?:e)?|Jul|jul(?:y)?|Aug|aug(?:ust)?|Sep|sep(?:tember)?|Oct|oct(?:ober)?|(Nov|nov|Dec|dec)(?:ember)?)$': 'MONTH',
            r'^(t|T)oday|(t|T)omorrow|(t|T)mr|(Mon|mon|Tue(?:s)?|tue(?:s)?|Thu(?:rs)?|thu(?:rs)?|Fri|fri|Sun|sun(?:day)?)|(Wed|wed(?:nesday)?)|(Sat|sat(?:urday)?)': 'DAY',
            r'^this|next|following$': 'DAY_ADJ',
            r'^([0-9])(?:\.|:)?([0-5][0-9])$': 'TIME_24',
            r'^([01][0-9]|2[0-3])(?:\.|:)?([0-5][0-9])$': 'TIME_24',
            r'^(1[0-2]|0?[1-9])(?:\.|:)?(?:[0-5][0-9])?(am|pm|Am|Pm|AM|PM)$': 'TIME_12'
            }
reg_tagger = RegexpTagger(list(patterns.items()))

grammar = r"""
    MATCH_DAY:
    (<VB.*>|<JJ.*>)<.*>{<IN><DAY_ADJ>?<DAY>}
    (<VB.*>|<JJ.*>)<NN.*>*{<IN>?<DAY_ADJ>?<DAY>}
    {<DAY_ADJ>?<DAY>}<VB.*>
    <NN.*>{<IN><DAY_ADJ>?<DAY>}
    <IN><TO><VB.*>{<DAY_ADJ>?<DAY>}
    DATE_#:
    {<CD><MONTH><CD>?}
    {<CD><IN><MONTH><CD>?}
    {<CD>?<MONTH><CD>}
    MATCH_DATE:
    (<VB.*>|<JJ.*>)<.*>{<IN><DATE.*>}
    (<VB.*>|<JJ.*>)<NN.*>*{<IN>?<DATE.*>}
    {<DATE.*>}<VB.*>
    <IN><NN.*>*{<DATE.*>}
    <IN><TO><VB.*>{<DATE.*>}
    <NN.*>*{<IN><DATE.*>}
    MATCH_DATE_TIME:
    {<IN>?<MATCH_DATE><IN>?<TIME.*><IN>?}
    {<IN>?<TIME.*><IN>?<MATCH_DATE><IN>?}
    (<VB.*>|<JJ.*>|<NNP>)<.*>{<IN>?<TIME.*><IN>?<DATE.*>}
    {<TIME.*><IN>?<DATE.*><IN>?}<VB.*>
    <IN><NN.*>*{<IN>?<TIME.*><IN>?<DATE.*>}
    <IN><TO><VB.*>{<IN>?<TIME.*><IN>?<DATE.*>}
    MATCH_DAY_TIME:
    {<IN>?<MATCH_DAY><IN>?<TIME.*><IN>?}
    {<IN>?<TIME.*><IN>?<MATCH_DAY><IN>?}
    (<VB.*>|<JJ.*>|<NNP>)<.*>{<IN>?<TIME.*><IN>?<DAY_ADJ>?<DAY>}
    {<DAY_ADJ>?<DAY><IN>?<TIME.*><IN>?}<VB.*>
    <IN><NN.*>*{<IN>?<TIME.*><IN>?<DAY_ADJ>?<DAY>}
    <IN><TO><VB.*>{<IN>?<TIME.*><IN>?<DAY_ADJ>?<DAY>}
    """
chunk_parser = nltk.RegexpParser(grammar)


def tokenize(sent):
    reg_out = reg_tagger.tag(word_tokenize(sent))
    tag_out = nltk.pos_tag(word_tokenize(sent))
    return [(token, rtag) if rtag in patterns.values() else (token, ttag) for (token, rtag), (_, ttag) in zip(reg_out, tag_out)]


statements_1 = ["buy hamster by 16 march",
                "reminder to buy mopiko by 16 of march",
                "going outfield march 16th",
                "go outfield on monday",
                "Go outfield on monday 180822",
                "Find out where is Casey tmr",
                "Date with Casey tmr",
                "Bring Casey out to orchard monday",
                "Tmr bring a set of lightsticks"]
statements_2 = ["buy hamster by tomorrow 1830",
                "reminder to buy mopiko by next monday 1830",
                "going outfield 3pm on monday",
                "Go outfield on monday 930",
                "Find out where is Casey 1330 next wed",
                "Date with Casey 2pm tmr",
                "Finish eco slides by 1500 tmr",
                "Bring Casey out to orchard tmr 1300",
                "Tmr 0800 bring a set of lightsticks"]


def gen_readable_str(a, time=None):
    dumb_str = str()
    date_str = str()
    for lf in a.leaves():
        pos = lf[1]
        val = lf[0].lower()

        if pos == 'DAY':
            if val == 'tmr':
                date_str += 'tomorrow'
            else:
                date_str += val
        elif pos == 'TIME_24':
            time_str = val.replace(':', "").replace('.', "")
            if len(time_str) == 3:
                time_str = time_str[0] + ':' + time_str[1:]
            else:
                time_str = time_str[:2] + ':' + time_str[2:]
        elif pos == 'TIME_12':
            time_str = val.replace(':', "").replace('.', "")
            if len(time_str) == 5:
                time_str = time_str[0] + ':' + time_str[1:]
            elif len(time_str) == 6:
                time_str = time_str[:2] + ':' + time_str[2:]
        elif pos == 'DAY_ADJ':
            date_str = val + ' ' + date_str

        elif pos in ('CD', 'MONTH'):
            date_str = date_str + val + ' '
        # else:
        #     print(pos)

    if time:
        dumb_str = date_str + ', ' + time_str
    else:
        dumb_str = date_str
    return dumb_str


def match_date(statement):
    tokenized_statement = tokenize(statement)
    tree = chunk_parser.parse(tokenized_statement)

    date = None
    time = None
    text = str()

    for a in tree:
        if isinstance(a, nltk.tree.Tree):
            label = a.label()
            if label in ("MATCH_DATE_TIME", "MATCH_DAY_TIME"):
                date_time, _ = cal.parseDT(
                    datetimeString=gen_readable_str(a, True))
                date = date_time.date()
                time = date_time.time()
            elif label in ("MATCH_DAY", "MATCH_DATE"):
                date_time, _ = cal.parseDT(
                    datetimeString=gen_readable_str(a))
                date = date_time.date()
            else:
                pass
        else:
            if text:
                text += ' '
            text += a[0]

    if date:
        return {'deadline': date, 'time_by': time, 'text': text}
    else:
        return None
