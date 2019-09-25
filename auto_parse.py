from bs4 import BeautifulSoup 
import re
import json
from pprint import pprint
global_re = {'.attrs':re.compile('\.[^\.]+')}
global_option = ('.clicked','.download','.attrs')
def find_item_bs(global_bs,all_tag_text,label_dict):
    ll = []
    self_attrs = {key:tuple(label_dict[key]) for key in label_dict if key.find('.attrs') != -1}
    for i in self_attrs:
        label_dict.pop(i)
    cut_href = lambda x:[i for i in  global_re['.attrs'].findall(x) if i not in global_option][0][1:]
    href_tuple = [(cut_href(key),val) for key,val in label_dict.items() if key.find('.')!=-1]
    other_dict = {key:val for key,val in label_dict.items() if key.find('.')==-1}
    hrefs_list = []
    for bs,bs_text in all_tag_text:
        bs_list = bs.find_all()
        ts = [0]*len(href_tuple)
        for ibs in bs_list:
            for i,(k,v) in enumerate(href_tuple):
                if re.search(v,ibs.attrs.get(k,'')):
                    ts[i] = 1
        if sum(ts) == len(href_tuple):
            hrefs_list.append((bs,bs_text))
    counter_dict = {i:0 for i in other_dict.keys()}
    for bs,bs_text in hrefs_list:
        for key,label in other_dict.items():
            if not re.search(label,bs_text):
                break 
            else:
                counter_dict[key] += 1
        else:
            ll.append(bs)
    for key,value in counter_dict.items():
        if value is 0:
            print(f'{key} is not matched correctly.')
    try:
        item_bs = ll[-1]
    except Exception as e:
        print("*"*45,"\nhtml has write in debug.html\n","*"*45)
        open('debug.html','w').write(str(global_bs))
        raise Exception(e)
    tag_type = item_bs.name
    item_attrs = {key:' '.join(item_bs.attrs[key]) for key in item_bs.attrs }
    # print(item_attrs)
    k = global_bs.find_all([tag_type],**item_attrs)
    print('自动匹配项数',len(k))
    all_item_tag = item_bs.find_all()
    all_item_tag.insert(0,item_bs)
    lables_attrs = {key:find_attrs_label(item_bs,all_item_tag,key,val) for key,val in label_dict.items()}
    lables_attrs.update(self_attrs)
    pprint(lables_attrs)
    return {'item_tag':tag_type,'item_attrs':item_attrs,'labels_attrs':lables_attrs}

def find_attrs_label(item_bs,all_item_tag,key,label):
    ll = []
    if key.find('.') == -1:
        for i in all_item_tag:
            if re.search(label,i.text):
                ll.append(i)
        try:
            label_bs = ll[-1]
        except Exception as e:
            print(item_bs)
            print(key,"not matched correctly")
            raise Exception(e)
        attrs = pure_attrs(label_bs.attrs)
        tag_type = label_bs.name
        k = item_bs.find_all([tag_type],**attrs)
        mark_type = 0
        if key == 'comment':
            print(label_bs)
            # exit()
    if key.find('.') != -1 or len(k) != 1:
        mark_type,content = find_attrs_label2(item_bs,all_item_tag,key,label)
    else:
        content = tag_type,attrs
    t = parse_label(item_bs,(mark_type,content))
    if len(t)!=1:
        print('warning',t,label)
    return mark_type,content

def find_attrs_label2(item_bs,all_item_tag,key,label):
    ll = []
    if key.find('.')!=-1:
        href = [i for i in  global_re['.attrs'].findall(key) if i not in global_option][0][1:]
        is_href = True
        for i in all_item_tag:
            if has_href(i,href,label):
                ll.append(i)
    else:
        for i in all_item_tag:
            if re.search(label,i.text):
                ll.append(i)
        is_href = False
    ll.sort(key=lambda x:len(str(x)))
    mark_type = 0
    #进行mark_type == 1 的尝试
    try:
        label_bs0 = ll[0]
    except Exception as e:
        print(item_bs)
        print(key,"not matched correctly")
        raise Exception(e)
    tag_type0 = label_bs0.name
    content = tag_type0,pure_attrs(label_bs0.attrs)
    bs_1 = label_bs0.find_all()

    if bs_1 and not is_href:
        bs = bs_1[0]
        tag_type = label_bs0.name
        tag_type_1 = bs.name
        attrs = pure_attrs(bs.attrs)
        c = tag_type,tag_type_1,attrs
        t = parse_label(item_bs,(1,c))
        if len(t) == 1:
            mark_type,content = 1,c
    if mark_type is 0 and not is_href:
        #进行mark_type==2的尝试
        item_parent = label_bs0.find_parent()
        if item_parent.text.find(label) != -1:
            tag_type = item_parent.name
            attrs = pure_attrs(item_parent.attrs)
            attrs_child = pure_attrs(label_bs0.attrs)
            t = findAll_bs(item_parent,tag_type0,attrs_child,recursive=False)
            for i,s in enumerate(t):
                if re.search(label,s.text):
                    nn = i 
            c = tag_type,attrs,tag_type0,attrs_child,nn
            t = parse_label(item_bs,(2,c))
            if re.search(label,t[0]):
                mark_type,content = 2,c
    if mark_type is 0 and is_href:
        #进行mark_type==3的尝试
        
        href_type = has_href(label_bs0,href,label)
        if href_type == 'child':
            
            d = {href:label}
            bs_list = label_bs0.find_all([],**d,recursive=False)
            # if len(bs_list) == 1:
            bs_child = bs_list[0]
            tag_child = bs_child.name
            child_attrs = pure_attrs(bs_child.attrs)
            c = href_type,href,tag_type0,label_bs0.attrs,tag_child,child_attrs
        else:
            attrs = pure_attrs(label_bs0.attrs)
            c = href_type,href,tag_type0,attrs
        t = parse_label(item_bs,(3,c))
        if len(t) == 1:
            mark_type,content = 3,c
    if mark_type is 0 and is_href:
        print(key)
        print(c)
        raise Exception("matched error 0001")
    return mark_type,content
def pure_attrs(attrs):
    attrs_keys = ('class','target','style')
    ff =  {key:value for key,value in attrs.items() if key in attrs_keys}
    return ff
def has_href(bs,href,label):
    t = re.search(label,bs.attrs.get(href,'hfefefe'))
    if t:
        return 'attrs' 
    else:
        d = {href:label}
        bs_list = bs.find_all([],**d)
        if bs_list:
            return 'child'
    return None
def parse_label(item_bs,mark):
    mark_type,content = mark 
    if mark_type is 0:
        '''<h3 class="course-card-name">Go开发短地址服务</h3>'''
        '''Go开发短地址服务'''
        tag_type,attrs = content
        t = findAll_bs(item_bs,tag_type,attrs)
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
        tag,attrs,tag2,attrs2,nn = content
        div = findAll_bs(item_bs,tag,attrs)
        if div:
            div = div[0]
            spans = findAll_bs(div,tag2,attrs2,recursive= False)
            result = [spans[nn].text]
        else:
            result = []
    elif mark_type is 3:
        
        if content[0] == 'child':
            '''<div class="course-card-container"> <a target="_blank" href="/learn/1150" class="course-card"> </a> </div>'''
            _,href,tag_div,attrs_p,tag_a,attrs_c = content
            bsp = findAll_bs(item_bs,tag_div,attrs_p)
            if len(bsp) == 0:
                bsp = item_bs
            else:
                bsp = bsp[0]
            bs_list = findAll_bs(bsp,tag_a,attrs_c)
            result = list(set([i.attrs[href] for i in bs_list if i.attrs.get(href,None)]))
        elif content[0] == 'attrs':
            '''<a target="_blank" href="/learn/1150" class="course-card"> </a>'''
            _,href,tag_a,attrs = content
            bs_list = item_bs.find_all([tag_a],**attrs)
            result = [i.attrs[href] for i in bs_list if i.attrs.get(href,None)]
        result = [i if isinstance(i,str) else ' '.join(i) for i in result]
    return result
def findAll_bs(bs,name,attrs,recursive=True):
    t = bs.findAll(name,attrs,recursive = recursive)
    def compare_attrs(attrs1,attrs2):
        for key in attrs1.keys():
            t = attrs2.get(key)
            if t:
                if isinstance(t,str) and t != attrs1[key]:
                    return False
                else:
                    if ''.join(attrs1[key]) != ''.join(t):
                        return False
        return True
    return [i for i in t if compare_attrs(attrs,i.attrs)]


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
    html = open('comment.html').read()
    bs = BeautifulSoup(html,'lxml')
    all_tag_text = [(i,i.text) for i in bs.find_all()]
    texts = {
        "course": "Go开发短地址服务",
        "level": "高级",
        "hot":"14\d\d",
        "profile":"2小时带你通过GO语言实现短地址服务。",
        "money":"免费",
        "course.href":"/learn/1150",
        "data.data-original":'//img\d*.mukewang.com/5d3e866e095df28306000338-240-135.png',
        "ddd":"收藏",
        "ddd.title":"收藏"
    }
    texts={
        "course": "Linux核心技能与应用",
        "level": "初级",
        "hot":"93",
        "comment":"2人评价",
        "profile":"一网打尽Linux必备核心技能，面试、升职必备的“敲门砖”。",
        "cost-price":"￥266.00",
        "discount-price":"￥229.00",
        "course.href":"/class/386.html",
        "course-price.attrs":(0,('div',{'class':'course-card-price'}))
    }
    auto_mark = find_item_bs(bs,all_tag_text,texts)
    print(auto_mark)
    rr = auto_parse_html(html,auto_mark)
    for i in rr:
        pprint(i)
    # html_e = open('element_bs.html').read()
    # bs = BeautifulSoup(html_e,'lxml')
    # print(bs.img.attrs)
