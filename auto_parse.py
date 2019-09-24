from bs4 import BeautifulSoup 
import re
import json
from pprint import pprint

def find_item_bs(global_bs,all_tag_text,label_dict):
    ll = []
    for bs,bs_text in all_tag_text:
        for label in label_dict.values():
            if bs_text.find(label) == -1:
                break 
        else:
            ll.append(bs)
    item_bs = ll[-1]
    tag_type = get_tag(item_bs)
    item_attrs = {key:' '.join(item_bs.attrs[key]) for key in item_bs.attrs }
    # print(item_attrs)
    k = global_bs.find_all([tag_type],**item_attrs)
    print('自动匹配项数',len(k))
    all_item_tag = item_bs.find_all()
    lables_attrs = {key:find_attrs_label(item_bs,all_item_tag,key,val) for key,val in label_dict.items()}
    pprint(lables_attrs)
    return {'item_tag':tag_type,'item_attrs':item_attrs,'labels_attrs':lables_attrs}
def find_attrs_label(item_bs,all_item_tag,key,label):
    ll = []
    if key.find('.') == -1:
        for i in all_item_tag:
            if i.text == label:
                ll.append(i)
        label_bs = ll[-1]
        attrs = label_bs.attrs
        attrs = {i:attrs[i] for i in attrs if i.find('href') == -1}
        tag_type = get_tag(label_bs)
        k = item_bs.find_all([tag_type],**attrs)
        mark_type = 0
    if key.find('.') != -1 or len(k) != 1:
        mark_type,content = find_attrs_label2(item_bs,all_item_tag,key,label)
    else:
        content = tag_type,attrs
    t = parse_label(item_bs,(mark_type,content))
    if len(t)!=1:
        print('warning',t,label)
    return mark_type,content
def get_item_type(item_name):
    if item_name.find('.') != -1:
        if item_name
    else:
        return 0
def find_attrs_label2(item_bs,all_item_tag,key,label):
    ll = []
    for i in all_item_tag:
        if i.text.find(label)!=-1:
            ll.append(i)
    ll.sort(key=lambda x:len(str(x)))
    mark_type = 0
    #进行mark_type == 1 的尝试
    label_bs0 = ll[0]
    tag_type0 = get_tag(label_bs0)
    content = tag_type0,label_bs0.attrs

    bs_1 = label_bs0.find_all()
    if bs_1:
        bs = bs_1[0]
        tag_type = get_tag(label_bs0)
        tag_type_1 = get_tag(bs)
        attrs = bs.attrs
        c = tag_type,tag_type_1,attrs
        t = parse_label(item_bs,(1,c))
        if len(t) == 1:
            mark_type,content = 1,c
    if mark_type is 0:
        #进行mark_type==2的尝试
        for bs in all_item_tag:
            t = bs.find_all([tag_type0],**content[1],recursive=False)
            right_label = False
            for i in t:
                if i.text == label:
                    right_label = True 
            if right_label:
                tag_type = get_tag(bs)
                attrs = bs.attrs 
                c = tag_type,attrs,tag_type0 
                t = parse_label(item_bs,(2,c))
                if len(t) == 1:
                    mark_type,content = 2,c
    return mark_type,content
def parse_label(item_bs,mark):
    mark_type,content = mark 
    if mark_type is 0:
        '''<h3 class="course-card-name">Go开发短地址服务</h3>'''
        '''Go开发短地址服务'''
        tag_type,attrs = content
        t = item_bs.find_all([tag_type],**attrs)
        result = [i.text for i in t]
    elif mark_type is 1:
        '''<span><i class="imv2-set-sns"></i>1343</span>'''
        '''1343'''
        tag_type,tag_type_i,attrs_i = content 
        all_tag = item_bs.find_all([tag_type])
        result = []
        for tag in all_tag:
            t = tag.find([tag_type_i],**attrs_i)
            if t:
                result.append(tag.text)
    elif mark_type is 2:
        '''<div class="course-card-info">
                    <span>高级</span><span><i class="imv2-set-sns"></i>1343</span>
                </div>
        '''
        '''高级'''
        tag,attrs,tag2 = content
        div = item_bs.find([tag],**attrs)
        result = []
        spans = div.find_all([tag2])
        for i in spans:
            if not i.find_all() and not i.attrs:
                result.append(i.text)
    return result
def get_tag(bs):
    s = str(bs)
    t = re.findall('\w+',s)
    return t[0]


def equal_attrs(attrs_origin,attrs_target):
    for key in attrs_target:
        t = attrs_origin.get(key)
        if t and t != attrs_target[key]:
            return False 
    return True


def auto_parse_html(html, auto_mark):
    bs = BeautifulSoup(html,'lxml')
    item_tag,item_attrs = auto_mark['item_tag'],auto_mark['item_attrs']
    labels_attrs = auto_mark['labels_attrs']
    t = bs.find_all([item_tag],**item_attrs)
    return [auto_parse_item(item_bs,labels_attrs) for item_bs in t]
def auto_parse_item(item_bs,labels_attrs):
    d = {key:','.join(parse_label(item_bs,value)) for key,value in labels_attrs.items()}
    return d


if __name__=='__main__':
    html = open('mooc.html').read()
    bs = BeautifulSoup(html,'lxml')
    all_tag_text = [(i,i.text) for i in bs.find_all()]
    texts = {
        "course": "Go开发短地址服务",
        "level": "高级",
        "hot":"1343",
        "profile":"2小时带你通过GO语言实现短地址服务。",
        "money":"免费"
    }
    auto_mark = find_item_bs(bs,all_tag_text,texts)
    print(auto_mark)
    rr = auto_parse_html(html,auto_mark)
    for i in rr:
        pprint(i)
