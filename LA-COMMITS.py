from __future__ import division
import datetime
import os
import copy

curl = 'curl -s --request GET https://review.lineageos.org/changes/?q=status:open+owner:"theh2o64@gmail.com"+project:LineageOS/'
target = ["android_kernel_cyanogen_msm8916","android_device_yu_tomato","android_device_yu_lettuce","android_device_yu_jalebi","android_device_cyanogen_msm8916-common"]

# Taken from http://stackoverflow.com/questions/8777753/converting-datetime-date-to-utc-timestamp-in-python/8778548#8778548
# and http://stackoverflow.com/questions/19068269/how-to-convert-a-string-date-into-datetime-format-in-python
def totimestamp(dt, epoch=datetime.datetime(1970,1,1)):
    td = dt - epoch
    return td.total_seconds()

def utctotimestamp(string):
	return totimestamp(datetime.datetime.strptime(string[:len(string)-4], "%Y-%m-%d %H:%M:%S.%f"))

def quicksort(t):
	if t == []: return []
	else:
		pivot = t[0]
		t1 = []
		t2 = []
		for x in t[1:]:
			if x<pivot:
				t1.append(x)
			else:
				t2.append(x)
	return quicksort(t1)+[pivot]+quicksort(t2)

def filter(liste):
	# Filter data
	tmp_liste = []
	cursor = 0
	for k in range(len(liste)):
		# print 'k = ' + str(k) + ' cursor = ' + str(cursor) + ' liste[cursor:k] = ' + liste[cursor:k]
		if liste[cursor:k].endswith('\n'):
			tmp_liste.append(liste[cursor:k-1])
			cursor = k
		if k == len(liste) - 1: tmp_liste.append(liste[cursor:k])
	return tmp_liste

def gather(remotes):
	project_out = []
	numbers_out = []
	subject_out = []
	topic_out = []
	updated_out = []
	count = 0
	# Gather raw data
	for i in remotes:
		project_out.append('LineageOS/' + i)
		numbers_out.append(os.popen(curl + i + '| sed 1d | jq --raw-output ".[] | ._number"').read())
		topic_out.append(os.popen(curl + i + '| sed 1d | jq --raw-output ".[] | .topic"').read())
		subject_out.append(os.popen(curl + i + '| sed 1d | jq --raw-output ".[] | .subject"').read())
		updated_out.append(os.popen(curl + i + '| sed 1d | jq --raw-output ".[] | .updated"').read())
		count += 1
	return (project_out,topic_out,numbers_out,subject_out,updated_out)

# Filter and un-split
def split(project_global, topic_global, numbers_global, subject_global,updated_global):
	project_local = [0]*len(target)
	topic_local = [0]*len(target)
	numbers_local = [0]*len(target)
	subject_local = [0]*len(target)
	updated_local = [0]*len(target)
	for k in range(len(target)):
		project_local[k] = project_global[k]
		topic_local[k] = filter(topic_global[k])
		numbers_local[k] = filter(numbers_global[k])
		subject_local[k] = filter(subject_global[k])
		updated_local[k] = filter(updated_global[k])
		# print 'k = ' + str(k) + ' | numbers_local[k] = ' + str(numbers_local[k])
	return (project_local,topic_local,numbers_local,subject_local,updated_local)

# Print data
def results():
	project_global,topic_global,numbers_global,subject_global,updated_global = gather(target)
	project,topic,numbers,subject,updated = split(project_global, topic_global, numbers_global, subject_global,updated_global)
	for k in range(len(target)):
		for j in range(len(numbers[k])):
			print('#####################')
			print('Project : ' + project[k])
			print('Change number : ' + numbers[k][j])
			print('Subject : ' + subject[k][j])
			print('Last updated : ' + updated[k][j])
			print('Timestamp : ' + str(utctotimestamp(updated[k][j])))
			if not topic[k][j] == 'null': print('Topic : ' + topic[k][j])
	for l in range(len(target)):
		print 'Number of commits for ' + project[l] + ' = ' + str(len(numbers[l]))

# Filtering to show last updated last
def order(topic_fil,numbers_fil,subject_fil,updated_fil):
	new_time = copy.deepcopy(updated_fil)
	dummy_copy = copy.deepcopy(updated_fil)
	new_time_sorted = copy.deepcopy(updated_fil)
	# Keep UTC alphabetic time sorted
	for k in range(len(target)): new_time_sorted[k] = quicksort(updated_fil[k])
	# Convert the timestamp UTC to numerical
	for k in range(len(target)):
		for j in range(len(numbers[k])):
			new_time[k][j] = (utctotimestamp(dummy_copy[k][j]),k,j)
	# Sort numerical timestamp
	for k in range(len(target)): new_time[k] = copy.deepcopy(quicksort(new_time[k]))
	# print str(new_time)
	topic_new = copy.deepcopy(topic_fil)
	numbers_new = copy.deepcopy(numbers_fil)
	subject_new = copy.deepcopy(subject_fil)
	time_swap(topic_fil, topic_new, new_time, new_time_sorted, dummy_copy)
	time_swap(numbers_fil, numbers_new, new_time, new_time_sorted, dummy_copy)
	time_swap(subject_fil, subject_new, new_time, new_time_sorted, dummy_copy)
	return topic_new,numbers_new,subject_new,new_time_sorted

def time_swap(old, new, time_ref, new_time_bis, old_time):
	for k in range(len(target)):
		for j in range(len(numbers[k])):
			# print 'old time = ' + str(old_time[k][j]) + ' | new time = ' + str(new_time_bis[k][j])
			new = old[time_ref[k][j][1]][time_ref[k][j][2]]

# Cherry picks
def picks():
	project_global,topic_global,numbers_global,subject_global,updated_global = gather(target)
	project,topic,numbers,subject,updated = split(project_global, topic_global, numbers_global, subject_global,updated_global)
	topic,numbers,subject,updated = order(topic,numbers,subject,updated)
	ret_topic = [0]*len(target)
	ret_numbers = [0]*len(target)
	ret_subject = [0]*len(target)
	for k in range(len(target)):
		# Reverse everything to show min first
		# TODO: Fix this in quicksort
		ret_topic[k] = copy.deepcopy(topic[k][::-1])
		ret_numbers[k] = copy.deepcopy(numbers[k][::-1])
		ret_subject[k] = copy.deepcopy(subject[k][::-1])
		for j in range(len(numbers[k])):
			print 'gerrit-cherry-pick ssh://h2o64@review.lineageos.org:29418/LineageOS/' + project[k] + ' ' + ret_numbers[k][j] + ' # ' + ret_subject[k][j] + ' - ' + updated[k][j]
	for l in range(len(target)):
		print '# Number of commits for ' + project[l] + ' = ' + str(len(ret_numbers[l]))
