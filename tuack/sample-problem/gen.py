#整个程序运行前将会先调用这个函数，可以不写
def init():
	from tuack import base
	#base.conf里面是预先读取好的conf.yaml数据，并对其进行了一些预处理
	#注意这段代码会【覆盖】data字段
	base.conf['data'] = []
	#这里是某种生成data参数的代码
	for i in range(1, 20):
		base.conf['data'].append({
			'cases' : [f"{i}-{j + 1}" for j in range(round(i ** 1.1))],
			'args' : {'n' : 20, 'm' : i}
		})
	#修改完conf以后需要保存
	base.save_json(base.conf)

from tuack import dmk
#如果使用random库，dmk会自动保存第一次运行的种子信息，之后运行会生成相同的数据
#如果需要重新随机，删除random_state即可
from random import randint

#生成数据的函数，参数分别是输出文件对象、参数获取器、上下文信息
def gen(fin, args, cont):
	# cont中有一些上下文信息
	dmk.log.debug(f"当前数据类型：{cont['folder']}")
	n = args['n']	#自动查找参数，优先查找测试点中的，找不到找全局，再找不到则是None
	m = args['m']
	tp = (cont['case'] if type(cont['case']) == int else int(cont['case'][-1])) & 1
	#往fin中输出即可
	fin.write(f"{n} {m}\n")
	edges = {(1, n)}
	for i in range(m - tp):
		while True:
			u = randint(1, n)
			v = randint(1, n)
			if u != v and (u, v) not in edges:
				break
		edges.add((u, v))
		fin.write(f"{u} {v}\n")
	if tp:
		fin.write(f'1 {n}\n')
	fin.write(''.join([chr(ord('a') + randint(0, 25)) for i in range(n)]) + '\n')

#以下是测试功能：
#可以把gen定义为编译并执行某个程序
# gen = dmk.Compile('cdl/gen.cpp')
#还可以把gen定义为直接运行某个程序或命令
# gen = dmk.Run('python cdl/gen.py')
#运行时会依次传入下列参数到argv中：
#1. 该测试点的args，按照conf中的定义顺序
#2. 全局args中未出现在该测试点中的参数，同样按照conf中的定义顺序
#3. 一个随机数种子，不改变代码时该种子不变
#4. 测试点名称（cases中的名字）、测试点类型（down、data、pre）

def vali(fout, args, cont, fin):
	# fout是标准输出，可以忽略；该参数是为了调用模式的一致性
	import re
	n = fin.int(args['n'])                  #单参数表示必须取等
	m = fin.int(1, args['m'], end = '\n')   #双参数表示左闭右闭区间
	#不加end表示后接严格一个空格，否则表示后接严格一个end
	# m = fin.intN(1, args['m'])            #等价写法
	#注意：行末空格的检验是严格的，因为做题人可能自己写特化的读入
	edges = set()
	for i in range(m):
		u = fin.int(1, n)
		v = fin.intN(1, n)
		assert(u != v)
		assert((u, v) not in edges)
		edges.add((u, v))
	#用正则表达式判断下一行是长度为n的小写字母串
	assert(re.match(r'^[a-z]{%d}$' % n, fin.strN()))

# vali = dmk.Compile('cdl/vali.cpp')
# vali = dmk.Run('python cdl/vali.py')
#validator也可以用类似于gen的方式调用
#返回值为非0表示校验失败，错误信息可以直接输出到stdout

# std = ('cdl', 'std')
#指定用于生成ans的程序名称，为conf.yaml中users的结构
# std = dmk.Compile('cdl/std.cpp')
# std = dmk.Run('python cdl/std.py')
# def std(fout, args, cont, fin):
#   a, b = map(int, fin.readline().split(' '))
#   fout.write(f"{a + b}\n")
#也可以和上述用法相同

# 增加一个regen功能，如果返回错误，则会重新调用gen和std
# 如果你不需要这个功能，不定义regen变量或函数即可
# 如果是外部调用版本，返回非零表示错误
# 和前面的函数相比，argv的最后多一个输出文件名
# 注意：输入文件用标准输入读，但输出文件需要你手动打开文件名对应的文件
# regen = dmk.Compile('cdl/regen.cpp')
# regen = dmk.Run('python cdl/regen.py')
# 如果是python函数版本，raise Exception表示错误
# python函数版本也多一个参数表示输出文件名
# def regen(fout, args, cont, fin, ans_name):
#   ans = int(open(ans_name).readline())
#   if ans == 0:
#     raise Exception('因为答案为0所以需要重造数据。')
#   a, b = map(int, fin.readline().split())
#   assert(a == b)
