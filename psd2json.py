# coding=UTF-8
from psd_tools import PSDImage
import sys
import os
import json
import collections
import codecs
import copy


buildpath = sys.argv[0]
psdName = sys.argv[1]
# 路径
path_work, _ = os.path.split(buildpath)
path_outPut = os.path.join(path_work, 'output')
path_res = os.path.join(path_work, 'res')
path_template = os.path.join(path_work, 'template')
# 配置文件的数据缓存
dic_temp = {}
dic_config = None



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
    
    jsonStr = json.dumps(tempDic, indent = 4, ensure_ascii = False)
    return jsonStr


#搜索图片所在路径
def _searchPngPath( pngName ):
    configDic = _loadConfigData(psdName)
    for path in configDic['searchPath']:
        findPath = path + '/' + pngName + '.png')
        if os.path.exists(os.path.join(configDic['sourceRootPath'], findPath)):
            return findPath
    print('Error: Cannot find the pic path of ', pngName + '.png')
    return 'default.png'


#转换头信息
def _decodeHeadInfo(psd):
    tempDic = _loadTemplateData('Header')
    tempDic['designHeight'] = psd.header.height
    tempDic['designWidth'] = psd.header.width
    tempDic['widgetTree']['options']['height'] = psd.header.height
    tempDic['widgetTree']['options']['width'] = psd.header.width
    return tempDic


#获取组件本地坐标
def _getLocalPos(layer):
    localPos = {'x1': layer.bbox.x1, 'x2': layer.bbox.x2, 'y1': layer.bbox.y1, 'y2': layer.bbox.y2}
    #转换成cocos坐标系
    rootHeight = layer._psd.header.height
    localPos['y1'] = rootHeight - layer.bbox.y2
    localPos['y2'] = rootHeight - layer.bbox.y1
    parentCCX1 = layer.parent.bbox.x1
    parentCCY1 = rootHeight - layer.parent.bbox.y2
    #转换成相对于父节点的局部坐标
    if not layer.parent.name == '_RootGroup':
        localPos['x1'] = localPos['x1'] - parentCCX1
        localPos['x2'] = localPos['x2'] - parentCCX1
        localPos['y1'] = localPos['y1'] - parentCCY1
        localPos['y2'] = localPos['y2'] - parentCCY1
    #
    return localPos


#转换panel数据
def _group2Panel(group, index):
    if not group.bbox:
        print('error in group %s' % group.name, 'no bbox')
        return
    
    tempDic = _loadTemplateData('Panel')
    localPos = _getLocalPos(group)
    transDic = {
        #common
        'name': 'pnl_%d' % index,
        'ZOrder': (len(group.parent.layers) - index) * 5,
        'height': group.bbox.height,
        'width': group.bbox.width,
        'opacity': group.opacity,
        'tag': index,
        'visible': group.visible,
        'x': localPos['x1'] + tempDic['options']['anchorPointX'] * group.bbox.width,
        'y': localPos['y1'] + tempDic['options']['anchorPointY'] * group.bbox.height,
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
            child = _group2Panel(group.layers[i], i)
            if child:
                tempDic['children'].append(child)
        #Label
        elif group.layers[i].text_data:
            child = _layer2Label(group.layers[i], i)
            if child:
                tempDic['children'].append(child)
        #ImageView
        else:
            child = _layer2ImageView(group.layers[i], i)
            if child:
                tempDic['children'].append(child)

    return tempDic


#转换ImageView数据
def _layer2ImageView(layer, index):
    tempDic = _loadTemplateData('ImageView')
    localPos = _getLocalPos(layer)
    layerName = layer.name.replace(' ', '') # 清除白空格
    transDic = {
        #common
        'name': 'img_%d' % index,
        'ZOrder': (len(layer.parent.layers) - index) * 5,
        'height': layer.bbox.height,
        'width': layer.bbox.width,
        'opacity': layer.opacity,
        'tag': index,
        'visible': layer.visible,
        'x': localPos['x1'] + tempDic['options']['anchorPointX'] * layer.bbox.width,
        'y': localPos['y1'] + tempDic['options']['anchorPointY'] * layer.bbox.height,
        #feature
        'fileNameData': {
            'path': _searchPngPath(layerName),
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
    localPos = _getLocalPos(layer)
    transDic = {
        #common
        'name': 'lbl_%d' % index,
        'ZOrder': (len(layer.parent.layers) - index) * 5,
        'colorB': layer.text_data.font_color['B'],
        'colorG': layer.text_data.font_color['G'],
        'colorR': layer.text_data.font_color['R'],
        'height': layer.bbox.height,
        'width': layer.bbox.width,
        'opacity': layer.opacity,
        'tag': index,
        'visible': layer.visible,
        'x': localPos['x1'] + tempDic['options']['anchorPointX'] * layer.bbox.width,
        'y': localPos['y1'] + tempDic['options']['anchorPointY'] * layer.bbox.height,
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
    if not(tempName in dic_temp):
        jsonFile = open(os.path.join(path_template, tempName + '.temp'), 'r')
        jsonStr = jsonFile.read()
        jsonFile.close()
        dic_temp[tempName] = json.loads(jsonStr, object_pairs_hook=collections.OrderedDict)
    return copy.deepcopy(dic_temp[tempName])


#加载配置数据
def _loadConfigData(pathName):
    global dic_config
    if not dic_config:
        jsonFile = open(os.path.join(path_res, pathName + '.conf'), 'r')
        jsonStr = jsonFile.read()
        jsonFile.close()
        dic_config = json.loads(jsonStr, object_pairs_hook=collections.OrderedDict)
    return dic_config


#---------------------------------------Main---------------------------------
#

#读取PSD
psd = PSDImage.load(os.path.join(path_res, psdName + '.psd'))
#生成Json
jsonStr = psd2Json(psd)
if not os.path.exists(os.path.join(path_outPut, psdName)):
    os.makedirs(os.path.join(path_outPut, psdName))
jsonFile = codecs.open(os.path.join(path_outPut, psdName, psdName + '.json'), "w+", 'utf-8')
jsonFile.write(jsonStr)
jsonFile.close()



