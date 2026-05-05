help = '''\
在任何tuack工程下运行，查看或编辑题目的主要信息。
如果不加-e是查看模式，题目信息依次是：
名称：题目的name，用于考试提交的文件名、OJ名称等
P/O/I：传统/提答/交互
1/0/-：partial score真/假/未设置
1/0/-：文件读写真/假/未设置
时间限制
空间限制
测试点数量
测试包数量
样例数量
预测试点数量
预测试包数量
标题：题目的title，用于OJ和考试的标题
'''

edit_keys = ['type', 'time limit', 'memory limit', 'name', 'title/zh-cn', 'file io', 'partial score']

from . import base, tools
from .base import log
import sys, yaml, shutil, time

def problem(conf, ind = 0):
	if ind <= 0:
		print(conf)
	else:
		print("%-15s%-1s%-1s%-1s%5s%8s%3d%3d%3d%3d%3d %s" % (
			conf['name'],
			{
				'program' : 'P',
				'output' : 'O',
				'interactive' : 'I'
			}.get(conf['type'], '-'),
			{
				False : 0,
				True : 1
			}.get(conf['partial score'], '-'),
			{
				False : 0,
				True : 1
			}.get(conf['file io'], '-'),
			conf.get('time limit', 'N/A'),
			conf.get('memory limit', 'N/A'),
			len(conf.test_cases),
			len(conf['data']),
			len(conf.samples),
			len(conf.pre_cases),
			len(conf['pre']),
			conf['title']['zh-cn'],
		))

def day(conf, ind = 0):
	if ind <= 0:
		print(conf)
	else:
		delta = (tools.to_time(conf.get('end time')) - tools.to_time(conf.get('start time'))).seconds
		print('%-10s%2d:%02d:%02d %s-%s' % (
			conf['name'],
			delta // 3600,
			delta // 60 % 60,
			delta % 60,
			conf.get('title', {}).get('zh-cn'),
			conf.get('subtitle', {}).get('zh-cn')
		))
	for i, p in enumerate(conf.sub, 1):
		print('  ' * ind + '[%02d]' % i, end = '')
		problem(p, ind + 1)
		if conf['subdir'][i - 1] != p['name']:
			print('  ' * ind + f"[WA]文件夹名{conf['subdir'][i - 1]}和子目录名称{p['name']}不一致")

def contest(conf, ind = 0):
	if ind <= 0:
		print(conf)
	for i, d in enumerate(conf.sub, 1):
		print('  ' * ind + '[%02d]' % i, end = '')
		day(d, ind + 1)
		if conf['subdir'][i - 1] != d['name']:
			print('  ' * ind + '[%02d]' % i + f"[WA]文件夹名{conf['subdir'][i - 1]}和子目录名称{d['name']}不一致")

def main(conf):
	def my_get(items, keys):
		for key in keys.split('/'):
			items = items[key]
		return items
	def my_set(items, keys, val):
		log.debug(f"{keys} {val}")
		keys = keys.split('/')
		for key in keys[:-1]:
			items = items[key]
		items[keys[-1]] = val
	if base.water_mark:
		for idx, line in enumerate(open(base.water_mark)):
			items = line.rstrip('\n').split('\t')
			key = items[-1]
			items = items[:-1]
			if len(items) != len(list(conf.probs())):
				raise Exception(f"第{idx + 1}行，字段为{key}，参数个数和题目数量不匹配。")
			if idx == 0:
				routes = items
				continue
			for route, prob, val in zip(routes, conf.probs(), items):
				if route != prob.route:
					raise Exception(f"第一行{route}和题目{prob.route}不匹配。")
				my_set(prob, key, yaml.safe_load(val))
		base.save_json(base.conf)
	if base.edit_mode:
		log.info('编辑模式不能修改【第一行信息】，字段信息不能出现【tab】！！')
		print('\t'.join([prob.route for prob in conf.probs()]) + '\t#')
		for key in edit_keys:
			print('\t'.join([yaml.safe_dump([my_get(prob, key)], allow_unicode = True)[2:-1] for prob in conf.probs()]) + '\t' + key)
	else:
		if type(conf) == base.Contest:
			contest(conf)
		elif type(conf) == base.Day:
			day(conf)
		elif type(conf) == base.Problem:
			problem(conf)
		else:
			log.error('未知的文件夹类型')

if __name__ == '__main__':
	if base.init():
		main(base.conf)
	else:
		log.info(help)
