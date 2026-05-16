help = u'''\
用于造数据，把gen.py放在problem目录下，然后运行：
python -m tuack.dmk [开关]
具体写法在gen.py有相关说明。
-s i,compile,g,run  跳过若干个步骤不执行。
                    i,init：初始化函数
                    c,compile：编译标程
                    g,gen：生成数据
                    v,vali：数据校验
                    r,run：运行标程
'''

from .base import log, pjoin
from . import base
import os, time, sys, random, traceback, uuid, platform, subprocess

folders = ['down', 'data', 'pre']
fmap = {'down' : 'samples', 'data' : 'data', 'pre' : 'pre'}

class Getter:
	def __init__(self, arg1, arg2):
		self.arg1 = arg1
		self.arg2 = arg2
		self.keys = set(arg1.keys()) | set(arg2.keys())
	def __getitem__(self, key):
		if key in self.keys: self.keys.remove(key)
		return self.arg1.get(key, self.arg2.get(key, None))
	def __del__(self):
		if len(self.keys):
			log.warning(f"下列数据字段并未使用：{','.join(self.keys)}")

class Run:
	def __init__(self, path):
		self.compiled = True
		self.exe = path
	def proc(self, args, **kwargs):
		if ret := subprocess.run(args, **kwargs).returncode:
			raise Exception(f"运行错误，返回值{ret}。")
	def run(self, args = None, fin = sys.stdin, fout = sys.stdout):
		if not self.compiled:
			log.info(f"编译程序{self.path}")
			self.proc(
				['g++', self.path, '-o', self.exe, '-std=c++17', '-O2', '-Wall', '-Wextra'] +
				([f"-Wl,--stack={int(base.conf.ml().B)}"] if base.system == 'Windows' else [])
			)
			self.compiled = True
		self.proc([self.exe] + (args if args else []), stdin = fin, stdout = fout)
	def __call__(self, fin, args, cont):
		self.run(list(args.arg1.values()) + [
			val for key, val in args.arg2.items() if key not in args.arg1
		] + [random.randint(0, 2 ** 31 - 1)] + list(cont.values()), fin = fin)
		args.keys = set()

class Compile(Run):
	def __init__(self, path):
		self.compiled = False
		self.path = path
		self.exe = pjoin(base.tmp_path, str(uuid.uuid4())[-12:])

import io
class Fin(io.TextIOWrapper):
	warn_float = False
	def next(self, no_except = False):
		if self.cn + 1 == len(self.buff):
			self.ln += 1
			self.cn = 0
			self.buff = self.readline()
			if self.buff == '':
				if no_except:
					return True
				else:
					raise Exception('需要继续读入，但到达了文件末尾。')
		else:
			self.cn += 1
	def __init__(self, *args, **kwargs):
		super(Fin, self).__init__(*args, **kwargs)
		self.ln = 0
		self.cn = -1
		self.buff = ''
	def cur(self):
		return self.buff[self.cn]
	def str(self, end = ' '):
		ret = ''
		self.next()
		while self.cur() != end:
			ret += self.cur()
			self.next()
		return ret
	def strN(self):
		return self.str(end = '\n')
	def number(self, v, a = None, b = None):
		if a is None:
			raise Exception('读入整数必须包含范围。')
		elif b is None:
			if v != a:
				raise Exception(f"读入的数据{v}必须等于{a}，但实际不等。")
		else:
			if not(a <= v <= b):
				raise Exception(f"读入的数据{v}必须在[{a}..{b}]中，但实际不在。")
		return v
	def int(self, a = None, b = None, end = ' '):
		return self.number(int(self.str(end)), a, b)
	def intN(self, a = None, b = None):
		return self.int(a, b, '\n')
	def float(self, a = None, b = None, end = ' '):
		if not Fin.warn_float:
			log.warning('Fin.float函数读入形如1e3的浮点数不会报错。')
			Fin.warn_float = True
		return self.number(float(self.str(end)), a, b)
	def floatN(self, a = None, b = None):
		return self.float(a, b, '\n')

def main(argv):
	global skip
	base.init()
	skip = set()
	flag = None
	for arg in argv:
		if arg == '-h':
			log.info(help)
			return
		elif flag == '-s':
			for key in arg.split(','):
				skip.add({
					'i' : 'init',
					'c' : 'compile',
					'g' : 'gen',
					'v' : 'vali',
					'r' : 'run'
				}.get(key, key))
			flag = None
		elif flag:
			log.error(f"错误的参数{flag}。")
			return
		elif arg.startswith('-'):
			flag = arg
		else:
			log.info(f"未知的传入信息{arg}。")
	for prob in base.conf.probs():
		back = os.getcwd()
		log.info(f"切换到目录`{prob.path}`运行数据生成。")
		os.chdir(prob.path)
		problem(prob)
		os.chdir(back)

def problem(conf):
	import gen
	if 'init' not in skip:
		if hasattr(gen, 'init'):
			gen.init()
		else:
			log.info('没有init函数，跳过执行。')
	std_exe = None
	if 'compile' not in skip:
		if not hasattr(gen, 'std'):
			log.info('没有std变量，将查找第一个expect能取到100的标程。')
			gen_std = None
			for user, codes in conf.get('users').items():
				for code, info in codes.items():
					expc = info.get('expected', '')
					if type(expc) == str:
						expc = [expc]
					for e in expc:
						if eval('100 ' + e) == True:
							gen_std = (user, code)
							break
					else:
						continue
					break
				if gen_std: break
			if not gen_std: log.warning('没有找到任何可能像标程的代码，请配置conf.yaml的users字段。')
		else:
			gen_std = gen.std
		if gen_std:
			std_exe = Compile(conf.get('users')[gen_std[0]][gen_std[1]].get('path'))
	if 'run' not in skip and not std_exe:
		log.warning('没有std.exe，无法生成输出文件。')

	if os.path.isfile('random_state'):
		random.setstate(eval(open('random_state').read()))
	else:
		open('random_state', 'w').write(str(random.getstate()))
	warnend_gen = False
	warnend_vali = False
	for folder in folders:
		os.makedirs(folder, exist_ok = True)
		for item in conf[fmap[folder]]:
			for case in item['cases']:
				log.info(f'数据类型{folder}，测试点{case}。')
				path_in = pjoin(folder, f"{case}.in")
				path_ans = pjoin(folder, f"{case}.ans")
				if hasattr(gen, 'gen'):
					if 'gen' not in skip and not item['args'].get('manual'):
						with open(path_in, 'w') as f:
							gen.gen(
								f,
								Getter(item.get('args', {}), conf.get('args', {})),
								{
									'case' : case,
									'folder' : folder
								}
							)
				elif not warnend_gen:
					log.warning('没有数据生成函数gen，跳过数据生成。')
					warnend_gen = True
				if hasattr(gen, 'vali'):
					if 'vali' not in skip:
						try:
							fin = Fin(open(path_in, 'rb'), encoding = 'utf-8')
							gen.vali(
								fin,
								Getter(item.get('args', {}), conf.get('args', {})),
								{
									'case' : case,
									'folder' : folder
								}
							)
							if not fin.next(True):
								raise Exception('校验函数结束以后还有内容没有读入。')
						except Exception as e:
							traceback.print_exc()
							log.error(f"在输入文件的第{fin.ln}行第{fin.cn + 1}个字符发生错误，错误信息如上所示。")
				elif not warnend_vali:
					log.warning('没有数据校验函数vali，跳过数据校验。')
					warnend_vali = True
				if std_exe:
					t = time.perf_counter()
					std_exe.run(fin = open(path_in), fout = open(path_ans, 'w'))
					log.info(f"标程用时：{time.perf_counter() - t}")
					ans = ' '.join([line.strip() for line in open(path_ans)])
					if len(ans) > 100: 
						ans = ans[:100] + f"（省略{len(ans) - 100}个字符。）"
					log.info('答案：' + ans)

if __name__ == '__main__':
	main(sys.argv[1:])
