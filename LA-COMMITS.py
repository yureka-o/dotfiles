from __future__ import division
import datetime
import os
import copy

curl = 'curl -s --request GET https://review.lineageos.org/changes/?q=status:open+owner:"theh2o64@gmail.com"+project:LineageOS/'
target = ["android_kernel_cyanogen_msm8916","android_device_yu_tomato","android_device_yu_lettuce","android_device_yu_jalebi","android_device_cyanogen_msm8916-common"]

# Blacklisting
commit_blacklist = [[''],[''],[''],[''],['']]
word_blacklist = ['','','','','']
id_black_per_rom = ['162848', '162848','163078','163078']
rom_black_per_rom = ['DU', 'SLIM','DU', 'SLIM'] # Easier than tuplet

# Extra commits
github_extra = ['h2o64/proprietary_vendor_yu/commit/3bf4e59ba071be2f162f4de695bce91afbf51406','h2o64/proprietary_vendor_yu/commit/daeec80a8fb17b415996c802d8bfbfe68398b258','h2o64/proprietary_vendor_yu/commit/d4ffa9bb0c3c1b8fb652c200bb05c6fc011dfae1','h2o64/proprietary_vendor_yu/commit/199fe6aa083d149709c85bcf0071363603e7f9db','h2o64/proprietary_vendor_yu/commit/cec0116114f2f3eed4e743b409e9abba8caa7c8e']
github_extra_branch = ['cm-14.1-ivy','cm-14.1-ivy','cm-14.1-ivy','cm-14.1-ivy','cm-14.1-ivy']
gerrit_extra = ['']

# Global variables
repos_count = len(target)
commits_count = [0]*repos_count

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

def get_patchset(commit_id):
	tmp = os.popen('ssh -p 29418 h2o64@review.lineageos.org gerrit query change:' + commit_id + ' --current-patch-set | grep "number: " | grep -v "' + commit_id + '"').read()
	return ((tmp.replace('number: ', '')).replace('\n','')).replace(' ','')

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
	project_local = [0]*repos_count
	topic_local = [0]*repos_count
	numbers_local = [0]*repos_count
	subject_local = [0]*repos_count
	updated_local = [0]*repos_count
	for k in range(repos_count):
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
	for k in range(repos_count):
		for j in range(commits_count[k]):
			print('#####################')
			print('Project : ' + project[k])
			print('Change number : ' + numbers[k][j])
			print('Subject : ' + subject[k][j])
			print('Last updated : ' + updated[k][j])
			print('Timestamp : ' + str(utctotimestamp(updated[k][j])))
			if not topic[k][j] == 'null': print('Topic : ' + topic[k][j])
	for l in range(repos_count):
		print 'Number of commits for ' + project[l] + ' = ' + str(len(numbers[l]))

# Filtering to show last updated last
def order(topic_fil,numbers_fil,subject_fil,updated_fil):
	new_time = copy.deepcopy(updated_fil)
	dummy_copy = copy.deepcopy(updated_fil)
	new_time_sorted = copy.deepcopy(updated_fil)
	# Keep UTC alphabetic time sorted
	for k in range(repos_count): new_time_sorted[k] = quicksort(updated_fil[k])
	# Convert the timestamp UTC to numerical
	for k in range(repos_count):
		for j in range(commits_count[k]):
			new_time[k][j] = (utctotimestamp(dummy_copy[k][j]),k,j)
	# Sort numerical timestamp
	for k in range(repos_count): new_time[k] = copy.deepcopy(quicksort(new_time[k]))
	# print str(new_time)
	topic_new = copy.deepcopy(topic_fil)
	numbers_new = copy.deepcopy(numbers_fil)
	subject_new = copy.deepcopy(subject_fil)
	time_swap(topic_fil, topic_new, new_time, new_time_sorted, dummy_copy)
	time_swap(numbers_fil, numbers_new, new_time, new_time_sorted, dummy_copy)
	time_swap(subject_fil, subject_new, new_time, new_time_sorted, dummy_copy)
	return topic_new,numbers_new,subject_new,new_time_sorted

def time_swap(old, new, time_ref, new_time_bis, old_time):
	for k in range(repos_count):
		for j in range(commits_count[k]):
			# print 'old time = ' + str(old_time[k][j]) + ' | new time = ' + str(new_time_bis[k][j])
			new = old[time_ref[k][j][1]][time_ref[k][j][2]]

# Cherry picks
def picks():
	project_global,topic_global,numbers_global,subject_global,updated_global = gather(target)
	project,topic,numbers,subject,updated = split(project_global, topic_global, numbers_global, subject_global,updated_global)
	for k in range(repos_count): commits_count[k] = len(numbers[k])
	topic,numbers,subject,updated = order(topic,numbers,subject,updated)
	ret_topic = [0]*repos_count
	ret_numbers = [0]*repos_count
	ret_subject = [0]*repos_count
	git_fetch = 'git fetch ssh://h2o64@review.lineageos.org:29418/'
	banned_rom_ind = []
	tmp = 'if '
	blacklist_word_count = [0]*repos_count
	word_blacklist_bool = True
	print 'CURRENT_DIR=$1'
	print 'CURRENT_DIR_NAME=$(basename $CURRENT_DIR)'
	for k in range(repos_count):
		# Reverse everything to show min first
		# TODO: Fix this in quicksort
		ret_topic[k] = copy.deepcopy(topic[k][::-1])
		ret_numbers[k] = copy.deepcopy(numbers[k][::-1])
		ret_subject[k] = copy.deepcopy(subject[k][::-1])
		print 'cd $CURRENT_DIR' + project[k].replace('LineageOS/android', '').replace('_','/')
		for j in range(commits_count[k]):
			if word_blacklist[k] not in ret_subject[k][j]:
				blacklist_word_count[k] += - 1
				word_blacklist_bool = False
			if ret_numbers[k][j] not in commit_blacklist[k]: # or word_blacklist_bool:
				for i in range(len(id_black_per_rom)):
					if ret_numbers[k][j] == id_black_per_rom[i]: banned_rom_ind.append(i)
				for m in banned_rom_ind:
					tmp += '[ ! $CURRENT_DIR_NAME == "' + rom_black_per_rom[m] + '" ]'
					if not m == banned_rom_ind[len(banned_rom_ind)-1]: tmp += ' || '
				if ret_numbers[k][j] in id_black_per_rom: print tmp + '; then'
				tmp = 'if [ '
				print git_fetch + project[k] + ' refs/changes/' + ret_numbers[k][j][-2] + ret_numbers[k][j][-1] + '/' + ret_numbers[k][j] + '/' + get_patchset(ret_numbers[k][j]) +' && git cherry-pick FETCH_HEAD # ' + ret_subject[k][j] + ' - ' + updated[k][j]
				if ret_numbers[k][j] in id_black_per_rom: print 'fi'
			# Reset
			word_blacklist_bool = True
			banned_rom_ind = []
		print 'cd $CURRENT_DIR'
	cherry = ''
	suffix = ''
	is_proprietary = False
	if not '' in github_extra:
		for ind in range(len(github_extra)):
			commit = github_extra[ind]
			if 'proprietary_vendor' in commit: is_proprietary = True
			for i in range(len(commit)):
				suffix = copy.deepcopy(commit[i:])
				if suffix.startswith('android_') or suffix.startswith('proprietary_vendor_'):
					suffix = copy.deepcopy(suffix[:len(suffix)-8-40])
					if is_proprietary: print 'cd ' + (suffix.replace('proprietary_','')).replace('_','/')
					else:  print 'cd ' + (suffix.replace('android_','')).replace('_','/')
					print 'git fetch https://github.com/' + commit[:-40-8] +  ' ' + github_extra_branch[ind]
					print 'git cherry-pick ' + commit[-40:]
					print 'cd $CURRENT_DIR'
					# Reset
					cherry = ''
					suffix = ''
					break
	commit_details = []
	if not '' in gerrit_extra:
		for m in gerrit_extra:
			tmp = os.popen('ssh -p 29418 h2o64@review.lineageos.org gerrit query change:' + m + ' | grep "project: "').read() # Project
			commit_details.append(((tmp.replace('project: ', '')).replace('\n','')).replace(' ',''))
			tmp = os.popen('ssh -p 29418 h2o64@review.lineageos.org gerrit query change:' + m + ' --current-patch-set | grep "number: " | grep -v "' + m + '"').read() # Patchset
			commit_details.append(((tmp.replace('number: ', '')).replace('\n','')).replace(' ',''))
			tmp = os.popen('ssh -p 29418 h2o64@review.lineageos.org gerrit query change:' + m + ' | grep "commitMessage: "').read() # Subject
			commit_details.append((tmp.replace('commitMessage: ', '')).replace('\n',''))
			tmp = os.popen('ssh -p 29418 h2o64@review.lineageos.org gerrit query change:' + m + ' | grep "lastUpdated: "').read() # Updated
			commit_details.append((tmp.replace('lastUpdated: ', '')).replace('\n',''))
			print 'cd $CURRENT_DIR' + commit_details[0].replace('LineageOS/android', '').replace('_','/')
			print git_fetch + commit_details[0] + ' refs/changes/' + m[-2] + m[-1] + '/' + m + '/' + commit_details[1] +' && git cherry-pick FETCH_HEAD #' + commit_details[2] + ' - ' + commit_details[3]
			print 'cd $CURRENT_DIR'
			commit_details = [] # Reset
	for l in range(repos_count):
		print '# Number of commits for ' + project[l] + ' = ' + str(len(ret_numbers[l]) - len(commit_blacklist[l]) + blacklist_word_count[l])
	print '# Number of extra commits  = ' + str(len(github_extra) + len(gerrit_extra))

if __name__ == '__main__':
    picks()
