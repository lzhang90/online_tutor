import numpy as np

from os import listdir
from os.path import isfile, join
import numpy as np
import csv
import math

data_path="C:/Users/ww/Desktop/双师/双师服务第三轮音频分析/data"
DEBUG = False
AUDIO_CLIP_FILTER = True
SESSION_LENGTH_MIN = 180
speaking_window_size = 2 # number of consecutive seconds of speaking
nospeaking_window_size = 2
MIN_SESSIONS_PER_PERSON = 3

class Audio_clip:

    def __init__(self):
        self.id = -1
        self.indicator_list = [] #the list of indicator that shows whether a student is speaking at the current second
        self.phase_lengths = []

    def read_clip_file(self, file_path):
        with open(file_path, 'r') as clip_file:
            self.id=file_path[file_path.rfind('/')+1:]
            newline = clip_file.readline()
            while newline:
                newline = newline.strip('\n')
                newline = newline.strip('\t')
                indicator = newline[len(newline)-1]
                self.indicator_list.append(indicator)
                newline = clip_file.readline()
        self.gen_phase_lengths()
        if DEBUG:
            print(self.descriptive())

    def gen_phase_lengths(self):
        speaking_accumulator = 0
        nospeaking_accumulator = 0
        for indicator in self.indicator_list:
            if indicator == '1':
                speaking_accumulator += 1
                if nospeaking_accumulator < nospeaking_window_size: #in calculating the length of speaking phase and the between nospeaking length is not long enough
                    speaking_accumulator += nospeaking_accumulator
                    nospeaking_accumulator = 0
                else:
                    print('report error 1')
            else:  # no speaking
                nospeaking_accumulator += 1
                if speaking_accumulator >= speaking_window_size: # the speaking length is enough, need to make sure whether the non speaking phase is big enough
                    if nospeaking_accumulator >= nospeaking_window_size: # the nonspeaking length is big enough to be used as the end of a speaking phase
                        self.phase_lengths.append(speaking_accumulator)
                        speaking_accumulator = 0
                        nospeaking_accumulator = 0
                else: #keep nospeaking, no need to do anything
                    speaking_accumulator = 0
                    nospeaking_accumulator = 0

    def get_phase_length_std(self):
        return np.std(self.phase_lengths)

    def descriptive(self):
        return [self.id, self.speaking_ratio(), np.mean(self.phase_lengths), np.std(self.phase_lengths), len(self.indicator_list)]

    def speaking_ratio(self):
        ones = 0
        zeros = 0
        for i in self.indicator_list:
            if i == '0':
                zeros += 1
            else:
                ones +=1
        return ones/((ones+zeros)*1.0)

class Student:

    def __init__(self):
        self.id = -1
        self.clip_list = []

    def set_id(self, id: int):
        self.id = id
    def add_audio_clip(self, clip_path):
        clip=Audio_clip()
        clip.read_clip_file(clip_path)
        if not (AUDIO_CLIP_FILTER and ((len(clip.indicator_list) < SESSION_LENGTH_MIN) or math.isnan(
                clip.get_phase_length_std()) or clip.get_phase_length_std() == 0)):
            self.clip_list.append(clip)

class Teacher:

    def __init__(self):
        self.id = -1
        self.clip_list = []

    def set_id(self, id: int):
        self.id = id
    def add_audio_clip(self, clip_path):
        clip=Audio_clip()
        clip.read_clip_file(clip_path)
        if not (AUDIO_CLIP_FILTER and ((len(clip.indicator_list) < SESSION_LENGTH_MIN) or math.isnan(clip.get_phase_length_std()) or clip.get_phase_length_std() == 0)):
            self.clip_list.append(clip)

    #calculate rate of comming back. to-do


def gen_index_file(file_path: str):
    audio_index=dict()
    with open(file_path,'r') as index_file:
        index_reader=csv.reader(index_file, delimiter=',')
        next(index_reader, None)
        for row in index_reader:
            stuid=str.strip(row[4])
            teacherid=str.strip(row[1])
            audio_path=str.strip(row[20])
            audio_name=audio_path[audio_path.rfind('/')+1:audio_path.rfind('.mp3')]
            audio_index[audio_name]=[stuid,teacherid]

    if '' in audio_index:
        del audio_index['']
    if DEBUG:
        print(audio_index)
    return audio_index

def convert_person_map_to_matrix(person_map: dict(), output_path, person_clips_name):
    with open(output_path+'/'+person_clips_name, mode='w', newline='') as csv_file:
        matrix_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        matrix_writer.writerow(['person_id', 'number_of_sessions','session_length_mean','session_length_median','session_speaking_ratio_mean', 'session_phase_length_mean', 'session_phase_length_std_mean'])
        for id in person_map:
            person=person_map[id]
            clips_num = 0
            speaking_ratio_list = []
            phase_length_mean_list = []
            phase_length_std_list = []
            session_length_list = []
            for clip in person.clip_list:
                clip_id, speaking_ratio, phase_length_mean, phase_length_std, session_length = clip.descriptive()
                clips_num += 1
                speaking_ratio_list.append(speaking_ratio)
                phase_length_mean_list.append(phase_length_mean)
                phase_length_std_list.append(phase_length_std)
                session_length_list.append(session_length)
            if(len(person.clip_list)>MIN_SESSIONS_PER_PERSON):
                matrix_writer.writerow([id,clips_num,np.mean(session_length_list),np.median(session_length_list),np.mean(speaking_ratio_list),np.mean(phase_length_mean_list),np.mean(phase_length_std_list)])

def gen_audio_clip_matrix(person_maps, output_path, audio_clip_output_name):
    with open(output_path+'/'+audio_clip_output_name, mode='w', newline='') as csv_file:
        matrix_writer=csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        matrix_writer.writerow(['id', 'session_length','speaking_ratio', 'phase_length_mean', 'phase_length_std'])
        for person_map in person_maps:
            for id in person_map:
                person = person_map[id]
                for clip in person.clip_list:
                    clipid, speaking_ratio_mean, phase_lengths_mean, phase_length_std_mean, session_length = clip.descriptive()
                    matrix_writer.writerow([clipid, session_length, speaking_ratio_mean, phase_lengths_mean, phase_length_std_mean])



audio_index=gen_index_file('C:/Users/ww/Desktop/双师/双师服务第三轮音频分析/原始音频链接-辅导数据.csv')
if DEBUG:
    print(audio_index.keys())
    print(len(audio_index.keys()))
file_num = 0
stu_map=dict()
teacher_map=dict()

for filename in listdir(data_path):
    # if the file name contains "(", it is a duplicated file
    if '(' in filename:
        continue

    audioname=filename.split('.')[0]

    #the corresponding student id of the audio cannot be found
    if audioname[:-2] not in audio_index:
        continue
    file_num += 1

    if DEBUG:
        print(audioname + ': ')
    stuid, teacherid=audio_index[audioname[:-2]]
    if audioname[-2:] == '学生':
        if stuid not in stu_map: #new student
            stu = Student()
            stu.set_id(stuid)
            stu_map[stuid] = stu
        else: # the student has been created
            stu = stu_map[stuid]
        stu.add_audio_clip(data_path+'/'+filename)
    else: #it is tutor
        if teacherid not in teacher_map:  # new student
            teacher = Teacher()
            teacher.set_id(teacherid)
            teacher_map[teacherid] = teacher
        else:  # the student has been created
            teacher = teacher_map[teacherid]
        teacher.add_audio_clip(data_path + '/' + filename)
convert_person_map_to_matrix(stu_map, 'C:/Users/ww/Desktop/双师/双师服务第三轮音频分析/output', 'stu_desc.csv')
convert_person_map_to_matrix(teacher_map, 'C:/Users/ww/Desktop/双师/双师服务第三轮音频分析/output', 'teacher_desc.csv')
print('The number of students: '+str(len(stu_map)))
print('The number of teachers: '+str(len(teacher_map)))
print('The number of tutoring sessions: '+str(file_num/2))

gen_audio_clip_matrix([stu_map], 'C:/Users/ww/Desktop/双师/双师服务第三轮音频分析/output', 'audio_info_stu.csv')
gen_audio_clip_matrix([teacher_map], 'C:/Users/ww/Desktop/双师/双师服务第三轮音频分析/output', 'audio_info_teacher.csv')
