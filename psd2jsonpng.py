# coding=UTF-8
from psd_tools import PSDImage
import sys
import os
import json
import collections


buildpath = sys.argv[0]
path, name = os.path.split(buildpath)
psd = PSDImage.load(os.path.join(path,'my_image.psd'))


#--------------------------------------------Png--------------------------
#

#导出psd中所有的图片, 主方法
def outputPngs(psd):
    _clearOutputDir()
    _saveLayerAsPng(psd)

#清空图片导出目录文件
def _clearOutputDir():
    files = os.listdir(os.path.join(path,'outputPngs'))
    for file in files:
        if file.endswith('.png'):
            os.remove(os.path.join(path,'outputPngs/'+file))


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
                pic_path = os.path.join(path,'outputPngs/%s.png' % layer_name)
                if not os.path.exists(pic_path):
                    layer_image = group.layers[i].as_PIL()
                    layer_image.save(pic_path)
            else:
                print('error in outputPngs, %s size is unexpected: <=0' % layer_name)


#------------------------------------------Json---------------------------
#

#解析数据到json, 主方法
def psd2Json(psd):
    tempDic = _decodeHeadInfo(psd)
    for i in range(len(psd.layers)):
        #Panel
        if hasattr(psd.layers[i], 'layers'):
            child = _group2Panel(psd.layers[i], i)
            if child:
                tempDic['widgetTree']['children'].append(child)
        #Label
        elif psd.layers[i].text_data:
            child = _layer2Label(psd.layers[i], i)
            if child:
                tempDic['widgetTree']['children'].append(child)
        #ImageView
        else:
            child = _layer2ImageView(psd.layers[i], i)
            if child:
                tempDic['widgetTree']['children'].append(child)
    
    jsonStr = json.dumps(tempDic, indent=4)
    return jsonStr


#搜索图片所在路径
def _searchPngPath( pngName ):
    return 'outputPngs/%s.png' % pngName #os.path.join(path, 'outputPngs/%s.png' % pngName)


#转换头信息
def _decodeHeadInfo(psd):
    tempDic = _loadTemplateData('Header')
    tempDic['designHeight'] = psd.header.height
    tempDic['designWidth'] = psd.header.width
    tempDic['widgetTree']['options']['height'] = psd.header.height
    tempDic['widgetTree']['options']['width'] = psd.header.width
    return tempDic


#转换panel数据
def _group2Panel(group, index):
    if not group.bbox:
        print('error in group %s' % group.name, 'no bbox')
        return
    
    tempDic = _loadTemplateData('Panel')
    transDic = {
        #common
        'name': 'pnl_%d' % index,
        'ZOrder': index,
        'height': group.bbox.height,
        'width': group.bbox.width,
        'opacity': group.opacity,
        'tag': index,
        'visible': group.visible,
        'x': group.bbox.x1 + tempDic['options']['anchorPointX'] * group.bbox.width,
        'y': group.bbox.y1 + tempDic['options']['anchorPointY'] * group.bbox.height,
        #feature
    }
    #set value
    for key in transDic:
        if key in tempDic['options']:
            tempDic['options'][key] = transDic[key]
    #children
    for i in range(len(group.layers)):
        #Panel
        if hasattr(group.layers[i], 'layers'):
            child = _group2Panel(group.layers[i], index)
            if child:
                tempDic['children'].append(child)
        #Label
        elif group.layers[i].text_data:
            child = _layer2Label(group.layers[i], index)
            if child:
                tempDic['children'].append(child)
        #ImageView
        else:
            child = _layer2ImageView(group.layers[i], index)
            if child:
                tempDic['children'].append(child)

    return tempDic


#转换ImageView数据
def _layer2ImageView(layer, index):
    tempDic = _loadTemplateData('ImageView')
    transDic = {
        #common
        'name': 'img_%d' % index,
        'ZOrder': index,
        'height': layer.bbox.height,
        'width': layer.bbox.width,
        'opacity': layer.opacity,
        'tag': index,
        'visible': layer.visible,
        'x': layer.bbox.x1 + tempDic['options']['anchorPointX'] * layer.bbox.width,
        'y': layer.bbox.y1 + tempDic['options']['anchorPointY'] * layer.bbox.height,
        #feature
        'fileNameData': {
            'path': _searchPngPath(layer.name),
            'plistFile': '',
            'resourceType': 0
        }
    }
    #set value
    for key in transDic:
        if key in tempDic['options']:
            tempDic['options'][key] = transDic[key]
    return tempDic


#转换Label数据
def _layer2Label(layer, index):
    tempDic = _loadTemplateData('Label')
    transDic = {
        #common
        'name': 'lbl_%d' % index,
        'ZOrder': index,
        'colorB': layer.text_data.font_color['B'],
        'colorG': layer.text_data.font_color['G'],
        'colorR': layer.text_data.font_color['R'],
        'height': layer.bbox.height,
        'width': layer.bbox.width,
        'opacity': layer.opacity,
        'tag': index,
        'visible': layer.visible,
        'x': layer.bbox.x1 + tempDic['options']['anchorPointX'] * layer.bbox.width,
        'y': layer.bbox.y1 + tempDic['options']['anchorPointY'] * layer.bbox.height,
        #feature
        'fontSize': layer.text_data.font_size,
        'text': layer.text_data.text,
    }
    #set value
    for key in transDic:
        if key in tempDic['options']:
            tempDic['options'][key] = transDic[key]
    return tempDic


#加载模版数据
def _loadTemplateData(tempName):
    jsonFile = open(os.path.join(path + '/Template', tempName + '.temp'), 'r')
    modeJsonStr = jsonFile.read()
    jsonFile.close()
    targetJsonObj = json.loads(modeJsonStr, object_pairs_hook=collections.OrderedDict)
    return targetJsonObj


#---------------------------------------Main---------------------------------
#

jsonStr = psd2Json(psd)
jsonFile = open(os.path.join(path,"output.json"), "w+")
jsonFile.write(jsonStr)
jsonFile.close()
outputPngs(psd)


