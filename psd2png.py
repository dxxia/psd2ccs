# coding=UTF-8
from psd_tools import PSDImage
import sys
import os


buildpath = sys.argv[0]
psdName = sys.argv[1]
# 路径
path_work, _ = os.path.split(buildpath)
path_outPut = os.path.join(path_work, 'output')
path_res = os.path.join(path_work, 'res')
path_outPutPngs = os.path.join(path_outPut, psdName, 'pngs')



#--------------------------------------------Png--------------------------
#

#导出psd中所有的图片, 主方法
def outputPngs(psd):
    _clearOutputDir()
    _saveLayerAsPng(psd)

#清空图片目录
def _clearOutputDir():
    if not os.path.exists(path_outPutPngs):
        os.makedirs(path_outPutPngs)
    files = os.listdir(path_outPutPngs)
    for file in files:
        if file.endswith('.png'):
            os.remove(os.path.join(path_outPutPngs, file))


#拆分图片
def _saveLayerAsPng(group):
    for i in range(len(group.layers)):
        if hasattr(group.layers[i],'layers'):
            #层容器
            _saveLayerAsPng(group.layers[i])
        elif not group.layers[i].text_data:
            #图片
            layer_name = group.layers[i].name
            if group.layers[i].bbox.width > 0 and group.layers[i].bbox.height > 0:
                layer_name = layer_name.replace('/', '_') # 替换目录字符
                layer_name = layer_name.replace(' ', '') # 清除白空格
                pic_path = os.path.join(path_outPutPngs, layer_name + '.png')
                if not os.path.exists(pic_path):
                    layer_image = group.layers[i].as_PIL()
                    layer_image.save(pic_path)
            else:
                print('Error: In outputPngs, %s size is unexpected: <=0' % layer_name)




#---------------------------------------Main---------------------------------
#

#读取PSD
psd = PSDImage.load(os.path.join(path_res, psdName + '.psd'))
#导出切图
outputPngs(psd)
#导出预览图
preview_image = psd.as_PIL()
preview_image.save(os.path.join(path_outPut, psdName, psdName + '.png'))



