from bs4 import BeautifulSoup 
import re
import json
from pprint import pprint
global_re = {'.attrs':re.compile('\.[^\.]+')}
global_option = ('.clicked','.download','.attrs')
def find_item_bs(global_bs,all_tag_text,label_dict):
    def include_self_attrs(bs):
        for mark_type,content in self_attrs.values():
            if mark_type == -1:
                tag0,attrs0 = content[0][0][:2]
            t = findAll_bs(bs,tag0,attrs0)
            if len(t) == 0 and not compare_attrs(attrs0,bs.attrs):
                return False
        return True
    def deal_attrs(val):
        if isinstance(val[0],int):
            return tuple(val)
        elif isinstance(val[0],str):
            #检查val最后一个元素，如果是字符串则意味着获取最终tag的某个属性，否则意味着获取文本
            if isinstance(val[-1],str):
                href = val[-1]
                val = val[:-1]
            else:
                href = None
            llt = []
            i = 0
            nn = len(val)
            while nn>i:
                if isinstance(val[i],str):
                    ltemp = list(val[i:i+2])
                    i+=2
                    if len(val)>i and isinstance(val[i],int):
                        ltemp.append(val[i])
                        i+=1 
                    else:
                        ltemp.append(0)
                    llt.append(ltemp)
            llt = [[i[0],pure_attrs(i[1]),i[2]] for i in llt]
            return -1,(tuple(llt),href)
        else:
            raise Exception('type error 0002')

    ll = []
    self_set_item = label_dict.get('__item__')
    label_dict = {k:v for k,v in label_dict.items() if not (k.startswith('__') and k.endswith('__'))}
    self_attrs = {key:deal_attrs(val) for key,val in label_dict.items() if not isinstance(val,str)}
    for i in self_attrs:
        label_dict.pop(i)
    if self_set_item:
        _,(items_mark,_) = deal_attrs(self_set_item)
        items_mark[-1][-1] = -1
        items_mark = 1,items_mark
        matched_items = findAll_block(global_bs,items_mark)

    cut_href = lambda x:[i for i in  global_re['.attrs'].findall(x) if i not in global_option][0][1:]
    href_tuple = [(cut_href(key),val) for key,val in label_dict.items() if key.find('.')!=-1]
    other_dict = {key:val for key,val in label_dict.items() if key.find('.')==-1}
    hrefs_list = []
    for bs,bs_text in all_tag_text:
        bs_list = bs.find_all()
        ts = [0]*len(href_tuple)
        for ibs in bs_list:
            for i,(k,v) in enumerate(href_tuple):
                if re.search(v,ibs.attrs.get(k,'')) or ibs.attrs.get(k,'').find(v) != -1:
                    ts[i] = 1
        if sum(ts) == len(href_tuple):
            hrefs_list.append((bs,bs_text))
    if len(hrefs_list) is 0:
        hrefs_list = all_tag_text
    counter_dict = {i:0 for i in other_dict.keys()}
    for bs,bs_text in hrefs_list:
        for key,label in other_dict.items():
            if (not re.search(label,bs_text)) and bs_text.find(label)==-1:
                break 
            else:
                counter_dict[key] += 1
        else:
            ll.append(bs)
    for key,value in counter_dict.items():
        if value is 0:
            print(f'{key} is not matched correctly.')
    try:
        ll.sort(key = lambda x:len(str(x)))
        item_bs = ll[0]

    except Exception as e:
        print("*"*45,"\nhtml has write in debug.html\n","*"*45)
        open('debug.html','w').write(str(global_bs))
        raise Exception(e)
    if not self_set_item:
        tag_type = item_bs.name
        item_attrs = pure_attrs(item_bs.attrs)
        matched_items = findAll_bs(global_bs,[tag_type],item_attrs)
    print('自动匹配项数',len(matched_items))
    all_item_tag = item_bs.find_all()
    all_item_tag.insert(0,item_bs)
    lables_attrs = {key:find_attrs_label(item_bs,all_item_tag,key,val) for key,val in label_dict.items()}
    lables_attrs.update(self_attrs)
    return {'items_mark':items_mark,'labels_attrs':lables_attrs}

def find_attrs_label(item_bs,all_item_tag,key,label):
    ll = []
    if key.find('.') == -1:
        for i in all_item_tag:
            if re.search(label,i.text) or i.text.find(label) !=-1:
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
            if re.search(label,i.text) or i.text.find(label) !=-1:
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
        print(label)
        item_parent = label_bs0.find_parent()
        if item_parent.text.find(label) != -1:
            tag_type = item_parent.name
            attrs = pure_attrs(item_parent.attrs)
            attrs_child = pure_attrs(label_bs0.attrs)
            t = findAll_bs(item_parent,tag_type0,attrs_child,recursive=False)
            for i,s in enumerate(t):
                if re.search(label,s.text) or s.text.find(label) !=-1:
                    nn = i 
            c = tag_type,attrs,tag_type0,attrs_child,nn
            t = parse_label(item_bs,(2,c))
            if re.search(label,t[0]) or t[0].find(label) !=-1:
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
    ff =  {key:value if not isinstance(value,str) else value.split() for key,value in attrs.items() if key in attrs_keys}
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
    result = []
    if mark_type == -1:
        div_attrs,href = content
        bs = item_bs
        for nt,(tag,attrs,i) in enumerate(div_attrs):
            bs = findAll_bs(bs,tag,attrs,recursive=False)
            if bs:
                bs = bs[i]
            else:
                if nt is 0 and compare_attrs(attrs,pure_attrs(item_bs.attrs)):
                    bs = item_bs 
                else:
                    break
        else:
            if href:
                r = bs.attrs.get(href,[])
                if isinstance(r,str):
                    result = [r]
                else:
                    result = [' '.join(r)]
            else:
                result = [bs.text]
    elif mark_type is 0:
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
        if len(div) == 0 and tag == item_bs.name and compare_attrs(attrs,pure_attrs(item_bs.attrs)):
            div = [item_bs]
        if div:
            div = div[0]
            spans = findAll_bs(div,tag2,attrs2,recursive= False)
            if spans:
                result = [spans[nn].text]
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
def compare_attrs(attrs1,attrs2):
    for key in attrs1.keys():
        t = attrs2.get(key)
        if t:
            if isinstance(t,str) and t != attrs1[key]:
                return False
            else:
                if ''.join(attrs1[key]) != ''.join(t):
                    return False
        else:
            return False
    return True
def findAll_bs(bs,name,attrs,recursive=True):
    t = bs.find_all(name,attrs,recursive = recursive)
    return [i for i in t if compare_attrs(attrs,i.attrs)]
def findAll_items(bs,name,attrs):
    def compare_attrs_item(attrs1,attrs2):
        for key,value in attrs1.items():
            temp = attrs2.get(key,set())
            for t in value:
                if t not in temp:
                    return False 
        else:
            return True

    t = bs.findAll(name,attrs)
    return [i for i in t if compare_attrs_item(attrs,i.attrs)]
def get_next_url(next_text,html,parent_url):
    bs = BeautifulSoup(html,'html5lib')
    all_tag_text = [(i,i.text) for i in bs.find_all()]
    bst = None
    all_tag_text.reverse()
    for t,s in all_tag_text:
        if s.find(next_text) !=-1:
            bst = t
            break
    if bst is None:
        return False 
    for i in range(10):
        if bst.attrs.get('href',None):
            urlt = bst.attrs['href']
            k = parent_url.split('/')
            if urlt.startswith('http:') or urlt.startswith('https:'):
                url_click = urlt 
            elif urlt.startswith('//'):
                url_click = parent_url.split(':')[0]+':'+urlt 
            elif urlt.startswith('/'):
                url_click = '/'.join(k[:3])+urlt
            elif urlt.startswith('?'):
                url_click = parent_url.split('?')[0]+urlt
            else:
                url_click = '/'.join(k[:-1])+'/'+urlt
            return url_click
        else:
            bst = bst.find_parent()
def equal_attrs(attrs_origin,attrs_target):
    for key in attrs_target:
        t = attrs_origin.get(key)
        if t and t != attrs_target[key]:
            return False 
    return True

def findAll_block(bs,items_mark):
    mark_type,content = items_mark 
    if mark_type is 0:
        item_tag,item_attrs = content 
        result = findAll_items(bs,item_tag,item_attrs)
    elif mark_type is 1:
        first_tag = True
        bs0 = bs
        for item_tag,item_attrs,n in content:
            if first_tag:
                recursive=True 
                first_tag = False 
            else:
                recursive=False
            result = findAll_bs(bs0,item_tag,item_attrs,recursive=recursive)
            if len(result) <= n:
                result = []
                break
            if n>=0:
                bs0 = result[n]

    return result
def auto_parse_html(html, auto_mark):
    bs = BeautifulSoup(html,'lxml')
    items_mark = auto_mark['items_mark']
    labels_attrs = auto_mark['labels_attrs']
    # t = findAll_items(bs,[item_tag],item_attrs)
    t = findAll_block(bs,items_mark)
    return [auto_parse_item(item_bs,labels_attrs) for item_bs in t]
def auto_parse_item(item_bs,labels_attrs):
    fget = lambda x:x[0] if len(x)>0 else ''
    d = {key:fget(parse_label(item_bs,value)) for key,value in labels_attrs.items()}
    return d

def debug_list_html():
    html = open('comment.html').read()
    bs = BeautifulSoup(html,'lxml')
    all_tag_text = [(i,i.text) for i in bs.find_all()]

    texts={
        "course": "Linux核心技能与应用",
        "level": "初级",
        "hot":"93",
        "comment":"2人评价",
        "profile":"一网打尽Linux必备核心技能，面试、升职必备的“敲门砖”。",
        "cost-price":"￥266.00",
        "discount-price":"￥229.00",
        "course.href":"/class/386.html",
        "course-price":('div',{'class':'course-card-price'}),
        "__next__":"下一页",
        # "__item__":('div',{'class':"shizhan-course-wrap l  "})
    }
    auto_mark = find_item_bs(bs,all_tag_text,texts)
    print(auto_mark)
    rr = auto_parse_html(html,auto_mark)
    pprint((rr))
    print(len(rr))
def debug_course_html():
    html = open('/home/yxs/F/pythonAPP/browser_crawler/debug.html').read()
    bs = BeautifulSoup(html,'html5lib')
    all_tag_text = [(i,i.text) for i in bs.find_all()]

    texts={
        "name": ['td',{},1,'table',{},'tbody',{},'tr',{},'td',{},'a',{},'b',{}],
        "name_href": ['td',{},1,'table',{},'tbody',{},'tr',{},'td',{},'a',{},'href'],
        "comment": ['td',{},2,'a',{}],
        "time": ['td',{},3,'span',{}],
        "color_type": ['class'],
        "size": ['td',{},4],
        "upload": ['td',{},5],
        "download": ['td',{},6],
        "all_download": ['td',{},7],
        "author": ['td',{},8],
        "__item__":['table',{'class':"torrents"},'tbody',{},0,'tr',{}]
    }
    auto_mark = find_item_bs(bs,all_tag_text,texts)
    print(auto_mark)
    rr = auto_parse_html(html,auto_mark)
    pprint((rr[-1]))
if __name__=='__main__':
    # debug_course_html()
    # debug_course_html()
    html = open('/home/yxs/F/pythonAPP/browser_crawler/debug.html').read()
    t = get_next_url('下一页',html,'https://feefe.con/fef.html')
    print(t)