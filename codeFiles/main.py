from flask import Flask, jsonify, make_response, request
from pprint import pprint
import json
from classroom import * 
import datetime

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!!!'

def set_session_id_in_response(request, response):
  response['session']['id'] = request['session']['id'] # TODO
  response['scene']['name'] = request['scene']['name'] # TODO
  return response

def get_all_activeCourses(response,service):
  results = service.courses().list().execute()
  courses = results.get('courses', [])
  activeCourses=[]

  if not courses:
    print("No active courses")
  else:
    for course in courses:
      if course['courseState']=='ACTIVE':
        activeCourses.append(course)
  display = "You have "+str(activeCourses.__len__())+" active courses. "
  courseCount=1;
  for course in activeCourses:
    print(course['name'])
    display+="Course "+str(courseCount)+" , "
    display+=course['name']
    display+=". "
    courseCount+=1;
  response['prompt']['firstSimple']['speech'] = display
  return response

def get_all_archivedCourses(response,service):
  results = service.courses().list().execute()
  courses = results.get('courses', [])
  archivedCourses=[]

  if not courses:
    print("No archived courses")
  else:
    for course in courses:
      if course['courseState']=='ARCHIVED':
        archivedCourses.append(course)
  display = "You have "+str(archivedCourses.__len__())+" archived courses. "
  courseCount=1;
  for course in archivedCourses:
    print(course['name'])
    display+="Course "+str(courseCount)+" , "
    display+=course['name']
    display+=". "
    courseCount+=1;
  response['prompt']['firstSimple']['speech'] = display
  return response

def get_all_courseDetails(response, req, service):
  results = service.courses().list().execute()
  courses = results.get('courses', [])
  courseName = req["intent"]["params"]["coursename"]["resolved"]
  courseName = courseName.lower()
  print(courseName)
  display=""
  flag=False
  if not courses:
    print("No courses found in classroom")
  else:
    for course in courses:
      tempVar = course['name'].lower()
      if tempVar.count(courseName)>0:
        print(course)
        flag=True
        display = "Getting details of the course "+course['name']+" . "
        display+="Course ID , "+course['id']+" . "
        display+="Course State , "+course['courseState']+" . "
        if 'descriptionHeading' in course and 'description'in course:
          display+="Course Description , "+course['descriptionHeading']+" . "+course['description']+" . "
        elif 'descriptionHeading' in course:
           display+="Course Description , "+course['descriptionHeading']+" . "
        elif 'description'in course:
          display+="Course Description , "+course['description']+" . "
        display+="Creation Time , "+course['creationTime']+" . "
        display+="Latest update Time , "+course['updateTime']+" . "
        if 'alternateLink' in course:
          display+="Alternate Link"+" , "+course['alternateLink']+" . "
        display+="Course Group Email ID , "+course['courseGroupEmail']+" . "
        display+="Calendar Id"+" , "+course['calendarId']+" . "
        if 'enrollmentCode' in course:
          display+="Enrollment Code , "+course['enrollmentCode']+" . "
        if 'room' in course:
          display+="Room , "+course['room']+" . "

        break
  if flag==False:
    display = "No course with coursename "+courseName+" found. "
  response['prompt']['firstSimple']['speech'] = display
  return response

def deadlineMissed(dueDate, dueTime):
  dateToday = datetime.datetime.utcnow(); 
  year=dueDate['year']
  month=dueDate['month']
  day=dueDate['day']
  hours=dueTime['hours']
  dateGiven = datetime.datetime(year,month,day,hours)
  flag = dateToday<dateGiven #due
  return flag

def get_all_courseDeadlines(response, req, service):
  results = service.courses().list().execute()
  courses = results.get('courses', [])
  courseName = req["intent"]["params"]["coursedeadlines"]["resolved"]
  courseName = courseName.lower()
  display=""
  temp=""
  deadlines=[]
  if not courses:
    print("No courses found in classroom")
  else:
    for course in courses:
      tempVar = course['name'].lower()
      if tempVar.count(courseName)>0:
        print(tempVar+" "+courseName)
        temp = course['name']
        result1 = service.courses().courseWork().list(courseId=course['id']).execute()
        if not result1:
          print("No courseWork found for "+course['name'])
          display = "No courseWork found for "+course['name']+". "
          response['prompt']['firstSimple']['speech'] = display
          return response

        if result1:
          for courseWork in result1["courseWork"]:
            f1=True
            f2=True
            if not courseWork.__contains__("dueDate"):
              f1=False
            else:
              dueDate = courseWork["dueDate"]
              if not courseWork.__contains__("dueTime"):
                f2=False
              else:
                dueTime = courseWork["dueTime"]
                if f1==True and f2==True:
                  if deadlineMissed(dueDate,dueTime):
                    deadlines.append(courseWork)
          break
  if temp=="":
    display = "No course with coursename "+courseName+" found. "
  else: 
    display+="You have "+str(len(deadlines))+" deadlines in the course "+temp+" . "
    deadlineCount=1;
    for deadline in deadlines:
      display+="Deadline "+str(deadlineCount)+" , "
      display+=deadline['title']+" . "
      deadlineCount+=1
  response['prompt']['firstSimple']['speech'] = display
  return response

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    if request.method == 'POST':
        req = request.json

        response = {
          "session": {
            "id": "example_session_id",
            "params": {}
          },
          "prompt": {
            "override": "false",
            "firstSimple": {
              "speech": "",
              "text": ""
            }
          },
          "scene": {
            "name": "SceneName",
            "slots": {},
            "next": {
              "name": "start"
            }
          }
        }
        response = set_session_id_in_response(req, response)
        service = setup()
        if req['handler']['name'] == 'activeCoursesHandler' :
          response = get_all_activeCourses(response,service)
        elif req['handler']['name'] == 'archivedCoursesHandler':
          response = get_all_archivedCourses(response, service)
        elif req['handler']['name'] == 'courseDetailsHandler':
          response = get_all_courseDetails(response, req, service)
        elif req['handler']['name'] == 'courseDeadlinesHandler':
          response = get_all_courseDeadlines(response, req, service)

        return jsonify(response)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
