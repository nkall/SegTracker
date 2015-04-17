# -*- coding: utf-8 -*-
from gluon import current
from datetime import datetime, timedelta
import pygal
from pygal.style import *

response.files.append(URL('static', 'css/segtracker.css'))
'''
' Main controller functions
'''
def index():
    if not auth.is_logged_in():
        redirect(URL('welcome'))
    token = current.session.token # get a dictionary containing the session information on the current user
    activities = db(db.activity.user_id == token['athlete']['id']).select(orderby=~db.activity.start_date)
    lastUpdated = token['athlete']['updated_at'].replace('T', ' ').replace('Z', '')
    return dict(token = token, activities = activities, lastUpdated = lastUpdated)

def user():
    return dict(form=auth())

def welcome():
    auth.settings.login_next = URL('index')
    authbutton = A(IMG(_src='/SegTracker/static/images/LogInWithStrava.png'), _href=URL('login'))
    return dict(authbutton=authbutton)

@auth.requires_login()
def login():
    if auth.is_logged_in():
        redirect(URL('index'))
    return dict(error='handle login error')

@auth.requires_login()
def activity():
    token = current.session.token
    act = db.activity(request.args(0))
    seg_effs = db(db.segment_effort.activity == act).select()
    return dict(activity=act, segment_efforts=seg_effs, token=token)

@auth.requires_login()
def segment():
    token = current.session.token
    segId = request.args(0)
    seg = db.segment(segId)
    actId = request.args(1)
    act = db.activity(actId)
    line_chart = genChart(token, seg, act)
    seg_efforts = db((db.segment_effort.segment == seg) &
                     (db.segment_effort.user_id == token['athlete']['id'])).select(orderby=db.segment_effort.start_date)
    if len(seg_efforts) < 1:
        redirect(URL('index'))
    if len(seg_efforts) > 150:
        startpoint = len(seg_efforts) - 150
    else:
        startpoint = 0
    dates = {}
    i = 0
    totalTime = 0.0
    for s in seg_efforts:
      totalTime += s.elapsed_time
      dates[i] = str(s.start_date)
      i += 1
    json_dates = json.dumps(dates)
    date_count = len(dates)
    effort_count = len(seg_efforts)
    return dict(segment=seg, token=token, chart=line_chart.render(), startpoint=startpoint,
                activity=act, dates=dates, json_dates=json_dates, totalTime=totalTime,
                n_dates=date_count, segId=segId, actId=actId, effort_count=effort_count)

@auth.requires_login()
def effort():
    token = current.session.token
    effort = db.segment_effort(request.args(0))
    act = db.activity(request.args(1))
    seg = db.segment(request.args(2))
    return dict(effort=effort, token=token, segment=seg, activity=act)

@auth.requires_login()
def update():
    client = Client(current.session.token['access_token'])
    token = current.session.token
    # Get new activities
    activities = client.get_activities()
    newActivities = []
    for activity in activities:
        #Add new activities to database
        if (db(db.activity.id == activity.id).count() < 1) and (activity.private is False):
            newActivities.append(activity.id)
    return dict(activities=newActivities, token=token)

def contributors():
    return locals()

def how_it_works():
    return locals()

@auth.requires_login()
def reset():
    token = current.session.token
    db(db.segment_effort.user_id == token['athlete']['id']).delete()
    db(db.activity.user_id == token['athlete']['id']).delete()

'''
' Helper functions
'''

def ajaxGetActivity():
    client = Client(current.session.token['access_token'])
    token = current.session.token
    newActId = request.get_vars.actid
    newActivity = client.get_activity(newActId)
    addActivity(newActivity)
    return newActivity.name


def listToHtml(list):
    return UL(*[LI(*entries) for entries in list])

#TODO: Make this generate dynamic charts
def ajax_getChart():
    token = current.session.token
    seg = db.segment(int(request.vars.segId))
    act = db.activity(int(request.vars.actId))

    seg_efforts = db((db.segment_effort.segment == seg) &
                     (db.segment_effort.user_id == token['athlete']['id'])).select(orderby=db.segment_effort.start_date)
    if len(seg_efforts) < 1:
        redirect(URL('index'))
    dates = {}
    i = 0
    for s in seg_efforts:
      dates[i] = s.start_date
      i += 1
    start = int(request.vars.start)
    end = int(request.vars.end)
    hasAvgLine = False
    hasMedLine = False
    hasCumMedLine = False
    hasCumAvgLine = False
    if request.vars.showAvg is not None:
        hasAvgLine = True
    if request.vars.showMed is not None:
        hasMedLine = True
    if request.vars.showCumAvg is not None:
        hasCumAvgLine = True
    if request.vars.showCumMedian is not None:
        hasCumMedLine = True

    line_chart = genChart(token, seg, act, dates[start], dates[end], hasAvgLine,
                          hasMedLine, hasCumAvgLine, hasCumMedLine, True)
    return '<figure style="text-align:center;">' + line_chart.render() + '</figure>'

def calcRollingAvg(newTime, oldAvg):
    decayCoefficient = 0.2
    newAvg = decayCoefficient * newTime + (1 - decayCoefficient) * oldAvg
    return newAvg

def genChart(token, seg, act, dateStart=None, dateEnd=None, hasAvgLine=True, hasMedLine=False,
             hasCumAvgLine=False, hasCumMedLine=False, isAjax=False):
    if isAjax:
        seg_efforts = db((db.segment_effort.segment == seg) &
                         (db.segment_effort.user_id == token['athlete']['id']) &
                         (db.segment_effort.start_date >= dateStart) &
                         (db.segment_effort.start_date <= dateEnd)).select(orderby=db.segment_effort.start_date)
    else:
        seg_efforts = db((db.segment_effort.segment == seg) &
                         (db.segment_effort.user_id == token['athlete']['id'])).select(orderby=db.segment_effort.start_date)
        if len(seg_efforts) > 150: #Limit segs with too many efforts for page load reasons
            seg_efforts = seg_efforts[-150:]

    efforts = []
    dates = []
    #Too few efforts means avg/median lines aren't useful
    if isAjax is False and len(seg_efforts) < 5:
        hasAvgLine = False

    #Initialize needed variables & lists for various lines
    if hasCumMedLine or hasMedLine:
        sortedTimes = []
        if hasMedLine:
            medEfforts = []
        if hasCumMedLine:
            cumMedEfforts = []
    if hasMedLine:
        #Range for rolling med changes based on # of efforts
        rollingRange = int(round(len(seg_efforts) / 10))
        #Snap ranges to hardcoded limits
        if rollingRange < 1:
            rollingRange = 1
        if rollingRange > 5:
            rollingRange = 5

    if hasAvgLine:
        avgEfforts = []
    if hasCumAvgLine:
        cumAvgEfforts = []
        cumTotal = 0

    #TODO: Make labels show ride name
    # Create data points for each segment effort
    for i, effort in enumerate(seg_efforts):
        effortLabel = effort.activity.name + ' (' + effort.start_date.strftime("%m/%d/%y") + ')'
        effortLink = URL('default', 'effort', args=[effort.id, act.id, seg.id])
        #Standard line
        efforts.append({'value': effort.elapsed_time,
                        'label': effortLabel,
                        'xlink': effortLink })
        dates.append(effort.start_date.date())
        if hasCumMedLine or hasMedLine:
            #Sort the times
            sortedTimes = insertTimeSorted(sortedTimes, effort.elapsed_time)
            #Calculate cumulative median
            if hasCumMedLine:
                cumMedEfforts.append({'value': calcMedian(sortedTimes),
                                     'label': effortLabel,
                                     'xlink': effortLink })
            #Calculate rolling median
            if hasMedLine:
                medEfforts.append({'value': calcRollingMedian(i, seg_efforts, rollingRange),
                                      'label': effortLabel,
                                      'xlink': effortLink })

        if hasAvgLine:
            #Calculate rolling average
            if i is 0:
                rollingAvg = effort.elapsed_time
            else:
                rollingAvg = calcRollingAvg(effort.elapsed_time, oldAvg)
            oldAvg = rollingAvg
            avgEfforts.append({'value': int(round(rollingAvg)),
                               'label': effortLabel,
                               'xlink': effortLink })
        if hasCumAvgLine:
            #Calculate cumulative average
            cumTotal += effort.elapsed_time
            cumAvgEfforts.append({'value': (cumTotal / (i+1)),
                                  'label': effortLabel,
                                  'xlink': effortLink })
    labels = genLabels(dates)
    #Generate chart
    line_chart = pygal.Line(style = BlueStyle,
                            width=1000,
                            height=600,
                            value_formatter = lambda x: str(timedelta(seconds=x)),
                            explicit_size=True,
                            show_legend=True,
                            legend_at_bottom=True,
                            show_x_guides=True,
                            x_label_rotation=20,
                            disable_xml_declaration=True,
                            print_values=False,
                            interpolate='hermite')
    line_chart.add('Effort Time', efforts)
    if hasAvgLine:
        line_chart.add('Moving Average', avgEfforts)
    if hasMedLine:
        line_chart.add('Moving Median', medEfforts)
    if hasCumAvgLine:
        line_chart.add('Cumulative Average', cumAvgEfforts)
    if hasCumMedLine:
        line_chart.add('Cumulative Median', cumMedEfforts)
    line_chart.x_labels = map(str, labels)
    return line_chart

def genLabels(dates):
    labels = []
    labels.append(dates[0].strftime("%m/%d/%y"))
    ld = len(dates)
    if ld == 3:
        labels.append(dates[ld / 2].strftime("%m/%d/%y"))
    elif ld > 3:
        hasLabels = False
        for i in range(12, 2, -1):
            if ((ld-1) % i) == 0:
                for j in range(1, i):
                    labels.append(dates[((ld)*j) / i].strftime("%m/%d/%y"))
                hasLabels = True
                break
        if hasLabels is False:
            labels.append(dates[(ld/3)].strftime("%m/%d/%y"))
            labels.append(dates[(ld*2 / 3)].strftime("%m/%d/%y"))
    if ld > 1:
        labels.append(dates[ld-1].strftime("%m/%d/%y"))
    return labels

def calcRollingMedian(i, efforts, medRange):
    upperLim = i + medRange
    lowerLim = i - medRange
    #Snap limits
    if upperLim > (len(efforts) - 1):
        upperLim = len(efforts) - 1
    if lowerLim < 0:
        lowerLim = 0
    sortedTimes = []
    for j in range(lowerLim, upperLim + 1):
        sortedTimes = insertTimeSorted(sortedTimes, efforts[j].elapsed_time)
    return calcMedian(sortedTimes)

def calcMedian(sortedTimes):
    if ((len(sortedTimes)) % 2) is 0:
         return (int(round((sortedTimes[int(len(sortedTimes) / 2.0) - 1] +
                                  sortedTimes[int(len(sortedTimes) / 2.0)]) / 2.0)))
    else:
        return (sortedTimes[int(round(len(sortedTimes) / 2.0) - 1)])

def insertTimeSorted(sortedTimes, time):
    isInserted = False
    for j, sortedTime in enumerate(sortedTimes):
        if time < sortedTime:
            sortedTimes[j:j] = [time]
            isInserted = True
            break
    if not isInserted:  #Worst or first time
        sortedTimes.append(time)
    return sortedTimes

#Adds an activity to database and returns a list of all new segment names
def addActivity(act):
    db.activity.insert(
        id = act.id,
        user_id = act.athlete.id,
        name = act.name,
        description = act.description,
        distance = float(act.distance),
        moving_time = act.moving_time.total_seconds(),
        elapsed_time = act.elapsed_time.total_seconds(),
        total_elevation_gain = int(act.total_elevation_gain),
        type = act.type,
        start_date = act.start_date_local,
        location_city = act.location_city,
        location_state = act.location_state,
        location_country = act.location_country,
        achievement_count = act.achievement_count,
        average_speed = float(act.average_speed),
        max_speed = float(act.max_speed)
        #map_object = db(db.map_object.id == act.map.id)
    )
    for segment_effort in act.segment_efforts:
        if (db(db.segment.id == segment_effort.segment.id).count() < 1) and \
            (segment_effort.segment.private is False):
            addSegment(act, segment_effort)
        addSegmentEffort(act, segment_effort)

def addSegment(act, eff):
    db.segment.insert(
        id = eff.segment.id,
        distance = float(eff.segment.distance),
        name = eff.segment.name,
        activity_type = eff.segment.activity_type,
        average_grade = eff.segment.average_grade,
        maximum_grade = eff.segment.maximum_grade,
        elevation_high = float(eff.segment.elevation_high),
        elevation_low = float(eff.segment.elevation_low),
        climb_category = eff.segment.climb_category,
        city = eff.segment.city,
        state = eff.segment.state,
        country = eff.segment.country,
    )

def addSegmentEffort(act, eff):
    db.segment_effort.insert(
        user_id = eff.athlete.id,
        elapsed_time = eff.elapsed_time.total_seconds(),
        moving_time = eff.moving_time.total_seconds(),
        start_date = eff.start_date_local,
        distance = float(eff.distance),
        activity = db.activity[act.id],
        segment = db.segment[eff.segment.id]
    )
