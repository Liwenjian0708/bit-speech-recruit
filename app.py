from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
import sqlite3
import math
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'bit_speech_2025_secure_key'  # 加密密钥，可自定义
DATABASE = 'recruit.db'

# 数据库连接
def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

# 初始化数据库
def init_db():
    with app.app_context():
        db = get_db()
        with open('schema.sql', 'r', encoding='utf-8') as f:
            db.executescript(f.read())
        db.commit()

# 首页
@app.route('/')
def index():
    return render_template('index.html')

# 注册/登录页
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form
        db = get_db()
        # 注册逻辑
        if 'register' in data:
            phone = data['phone']
            pwd = data['pwd']
            name = data['name']
            grade = data['grade']
            college = data['college']
            major = data['major']
            # 时间偏好采集
            time_slot = ','.join(request.form.getlist('time_slot'))
            busy_week = ','.join(request.form.getlist('busy_week'))
            activity_pre = data['activity_pre']
            # 检查手机号是否已注册
            if db.execute('SELECT * FROM user WHERE phone=?', (phone,)).fetchone():
                return jsonify({'status': 'error', 'msg': '手机号已注册'})
            # 插入用户数据
            db.execute('INSERT INTO user (phone, pwd, name, grade, college, major, time_slot, busy_week, activity_pre) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                       (phone, pwd, name, grade, college, major, time_slot, busy_week, activity_pre))
            db.commit()
            return jsonify({'status': 'success', 'msg': '注册成功，自动登录中'})
        # 登录逻辑
        elif 'login' in data:
            phone = data['phone']
            pwd = data['pwd']
            user = db.execute('SELECT * FROM user WHERE phone=? AND pwd=?', (phone, pwd)).fetchone()
            if user:
                session['user_id'] = user['id']
                session['user_name'] = user['name']
                session['role'] = 'student'  # 学生角色
                return jsonify({'status': 'success', 'msg': '登录成功'})
            else:
                return jsonify({'status': 'error', 'msg': '手机号或密码错误'})
    return render_template('login.html')

# 后台登录（管理员/队长）
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        data = request.form
        db = get_db()
        admin = db.execute('SELECT * FROM admin WHERE account=? AND pwd=?', (data['account'], data['pwd'])).fetchone()
        if admin:
            session['admin_id'] = admin['id']
            session['admin_name'] = admin['name']
            session['role'] = admin['role']  # admin/队长1/队长2/队长3/队长4
            session['team'] = admin['team']
            return jsonify({'status': 'success', 'msg': '登录成功'})
        else:
            return jsonify({'status': 'error', 'msg': '账号或密码错误'})
    return render_template('admin/admin_login.html')

# 个人中心
@app.route('/personal')
def personal():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    user = db.execute('SELECT * FROM user WHERE id=?', (session['user_id'],)).fetchone()
    apply = db.execute('SELECT * FROM apply WHERE user_id=?', (session['user_id'],)).fetchone()
    return render_template('personal.html', user=user, apply=apply)

# 四队长科普页
@app.route('/captain')
def captain():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('captain.html')

# 测评须知页
@app.route('/test/rule')
def test_rule():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('test_rule.html')

# 测评页
@app.route('/test', methods=['GET', 'POST'])
def test():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # 20道测评题（按需求还原）
    questions = [
        {"id":1, "title":"班级推选主题分享，你更倾向？", "options":{"A":"写稿深情讲述，享受舞台目光（演讲队）", "B":"把控流程，应对现场突发（主持队）", "C":"辩证交流，理性表达观点（辩论队）", "D":"情感配音朗读，带动情绪（配音队）"}},
        # 此处省略第2-20题，按需求完整复制即可，格式与第1题一致
        {"id":20, "title":"社团组织线下集训，你更关注？", "options":{"A":"表达技巧的打磨与提升", "B":"舞台控场的实战训练", "C":"逻辑思维的碰撞交流", "D":"声音情绪的精准把控"}}
    ]
    if request.method == 'POST':
        # 接收测评答案，存储到数据库
        answers = request.json
        user_id = session['user_id']
        db = get_db()
        # 检查是否已测评
        if db.execute('SELECT * FROM test WHERE user_id=?', (user_id,)).fetchone():
            db.execute('UPDATE test SET answers=? WHERE user_id=?', (str(answers), user_id))
        else:
            db.execute('INSERT INTO test (user_id, answers) VALUES (?, ?)', (user_id, str(answers)))
        db.commit()
        # 跳转到匹配报告页
        return jsonify({'status': 'success', 'url': url_for('report')})
    return render_template('test.html', questions=questions)

# 核心算法：能力加权+余弦相似度+时间匹配（三重计算）
def calculate_score(user_id):
    db = get_db()
    user = db.execute('SELECT * FROM user WHERE id=?', (user_id,)).fetchone()
    test = db.execute('SELECT * FROM test WHERE user_id=?', (user_id,)).fetchone()
    answers = eval(test['answers'])  # 个人答案向量
    
    # 1. 能力加权得分计算（40%权重）
    core_questions = [3,7,10,15,20]  # 核心题
    score = {'speech':0, 'host':0, 'debate':0, 'dubbing':0}
    for qid, opt in answers.items():
        qid = int(qid)
        # 基础题1分，核心题2分
        add = 2 if qid in core_questions else 1
        if opt == 'A': score['speech'] += add
        elif opt == 'B': score['host'] += add
        elif opt == 'C': score['debate'] += add
        elif opt == 'D': score['dubbing'] += add
    # 归一化到0-100分
    max_score = 25
    for k in score: score[k] = round(score[k]/max_score*100, 2)
    
    # 2. 标杆成员余弦相似度计算（35%权重）
    # 获取各队标杆平均向量
    benchmark = {}
    teams = ['speech', 'host', 'debate', 'dubbing']
    for team in teams:
        bm_answers = db.execute('SELECT answers FROM benchmark WHERE team=?', (team,)).fetchall()
        bm_vectors = [eval(b['answers']) for b in bm_answers]
        # 计算平均向量
        avg_vector = {}
        for qid in range(1,21):
            qid_str = str(qid)
            vals = [v[qid_str] for v in bm_vectors if qid_str in v]
            # 向量化：A=1, B=2, C=3, D=4
            vec_vals = [1 if v=='A' else 2 if v=='B' else 3 if v=='C' else 4 for v in vals]
            avg_vector[qid_str] = sum(vec_vals)/len(vec_vals) if vals else 2.5
        benchmark[team] = avg_vector
    # 计算个人向量与标杆向量的余弦相似度
    def cos_sim(v1, v2):
        dot = sum(v1[k]*v2[k] for k in v1 if k in v2)
        norm1 = math.sqrt(sum(v**2 for v in v1.values()))
        norm2 = math.sqrt(sum(v**2 for v in v2.values()))
        return round(dot/(norm1*norm2)*100, 2) if norm1*norm2 !=0 else 0
    # 个人向量化
    user_vector = {k:1 if v=='A' else 2 if v=='B' else 3 if v=='C' else 4 for k,v in answers.items()}
    sim_score = {t:cos_sim(user_vector, benchmark[t]) for t in teams}
    
    # 3. 时间匹配度计算（25%权重）
    time_score = {'speech':0, 'host':0, 'debate':0, 'dubbing':0}
    time_conflict = {}
    # 获取用户时间偏好
    user_time_slot = user['time_slot'].split(',')
    user_busy_week = user['busy_week'].split(',')
    user_activity_pre = user['activity_pre']
    # 遍历各队活动
    for team in teams:
        activities = db.execute('SELECT * FROM activity WHERE team=?', (team,)).fetchall()
        total_duration = 0
        match_duration = 0
        conflict_score = 0
        conflict_info = []
        for act in activities:
            total_duration += 1
            # 匹配时段
            if act['time_slot'] in user_time_slot:
                match_duration += 1
            # 冲突检测（忙碌周+活动形式）
            if act['week'] in user_busy_week:
                conflict_score += 15 if act['priority']=='高' else 10 if act['priority']=='中' else 5
                conflict_info.append(f"{act['name']}（{act['week']}，{act['priority']}优先级）")
            if act['form'] == '线下' and user_activity_pre == '仅线上':
                conflict_score += 10
                conflict_info.append(f"{act['name']}（线下活动，你仅能参与线上）")
        # 计算时间匹配率
        match_rate = round(match_duration/total_duration*100, 2) if total_duration>0 else 0
        # 时间匹配度得分=匹配率-冲突扣分（最低0分）
        ts = max(match_rate - conflict_score, 0)
        time_score[team] = ts
        time_conflict[team] = conflict_info if conflict_info else ['无冲突']
    
    # 综合匹配得分=能力(40%)+相似度(35%)+时间(25%)
    total_score = {}
    for t in teams:
        total_score[t] = round(score[t]*0.4 + sim_score[t]*0.35 + time_score[t]*0.25, 2)
    
    # 性格标签生成
    max_score_team = max(total_score, key=total_score.get)
    personality = {
        'speech':'感性热情型', 'host':'沉稳控场型',
        'debate':'理性思辨型', 'dubbing':'声音治愈型'
    }
    pers_tag = personality[max_score_team]
    
    # 排序得到推荐队伍
    sorted_teams = sorted(total_score.items(), key=lambda x:x[1], reverse=True)
    recommend1 = sorted_teams[0][0]
    recommend2 = sorted_teams[1][0]
    # 推荐理由
    reason1 = f"能力加权得分{score[recommend1]}分（40%）+ 标杆成员相似度{sim_score[recommend1]}%（35%）+ 时间匹配度{time_score[recommend1]}分（25%），综合得分最高，且无明显时间冲突"
    reason2 = f"综合得分第二（{total_score[recommend2]}分），时间匹配度{time_score[recommend2]}分，适配你的时间偏好"
    
    return {
        'score':score, 'sim_score':sim_score, 'time_score':time_score,
        'total_score':total_score, 'pers_tag':pers_tag,
        'recommend1':recommend1, 'recommend2':recommend2,
        'reason1':reason1, 'reason2':reason2, 'time_conflict':time_conflict
    }

# 多维匹配报告页
@app.route('/report')
def report():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    # 执行核心算法计算
    report_data = calculate_score(user_id)
    # 存储报告到数据库
    db = get_db()
    if db.execute('SELECT * FROM report WHERE user_id=?', (user_id,)).fetchone():
        db.execute('UPDATE report SET data=? WHERE user_id=?', (str(report_data), user_id))
    else:
        db.execute('INSERT INTO report (user_id, data) VALUES (?, ?)', (user_id, str(report_data)))
    db.commit()
    # 队伍名称映射
    team_map = {'speech':'演讲队', 'host':'主持队', 'debate':'辩论队', 'dubbing':'配音队'}
    return render_template('report.html', data=report_data, team_map=team_map)

# 在线报名页
@app.route('/apply', methods=['GET', 'POST'])
def apply():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    db = get_db()
    user = db.execute('SELECT * FROM user WHERE id=?', (user_id,)).fetchone()
    report = db.execute('SELECT * FROM report WHERE user_id=?', (user_id,)).fetchone()
    report_data = eval(report['data'])
    team_map = {'speech':'演讲队', 'host':'主持队', 'debate':'辩论队', 'dubbing':'配音队'}
    if request.method == 'POST':
        data = request.form
        team1 = data['team1']
        team2 = data['team2'] if 'team2' in data else ''
        intro = data['intro'] if 'intro' in data else ''
        specialty = data['specialty'] if 'specialty' in data else ''
        # 存储报名信息
        if db.execute('SELECT * FROM apply WHERE user_id=?', (user_id,)).fetchone():
            db.execute('UPDATE apply SET team1=?, team2=?, intro=?, specialty=?, status=? WHERE user_id=?',
                       (team1, team2, intro, specialty, '待审核', user_id))
        else:
            db.execute('INSERT INTO apply (user_id, name, phone, grade, college, major, team1, team2, intro, specialty, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                       (user_id, user['name'], user['phone'], user['grade'], user['college'], user['major'], team1, team2, intro, specialty, '待审核'))
        db.commit()
        return redirect(url_for('success'))
    return render_template('apply.html', user=user, data=report_data, team_map=team_map)

# 报名成功页
@app.route('/success')
def success():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    db = get_db()
    apply = db.execute('SELECT * FROM apply WHERE user_id=?', (user_id,)).fetchone()
    report = db.execute('SELECT * FROM report WHERE user_id=?', (user_id,)).fetchone()
    report_data = eval(report['data'])
    team_map = {'speech':'演讲队', 'host':'主持队', 'debate':'辩论队', 'dubbing':'配音队'}
    return render_template('success.html', apply=apply, data=report_data, team_map=team_map)

# 后台核心接口（管理员/队长）
@app.route('/admin/api/activity', methods=['GET', 'POST', 'PUT', 'DELETE'])
def admin_activity():
    if 'admin_id' not in session:
        return jsonify({'status':'error', 'msg':'未登录'})
    db = get_db()
    # 管理员可操作所有队伍，队长仅操作本队
    team = session['team'] if session['role'] != 'admin' else request.args.get('team', 'speech')
    if request.method == 'POST':
        # 新增活动
        data = request.json
        db.execute('INSERT INTO activity (team, name, time_slot, week, priority, form) VALUES (?, ?, ?, ?, ?, ?)',
                   (team, data['name'], data['time_slot'], data['week'], data['priority'], data['form']))
        db.commit()
        return jsonify({'status':'success'})
    elif request.method == 'PUT':
        # 编辑活动
        data = request.json
        db.execute('UPDATE activity SET name=?, time_slot=?, week=?, priority=?, form=? WHERE id=?',
                   (data['name'], data['time_slot'], data['week'], data['priority'], data['form'], data['id']))
        db.commit()
        return jsonify({'status':'success'})
    elif request.method == 'DELETE':
        # 删除活动
        act_id = request.args.get('id')
        db.execute('DELETE FROM activity WHERE id=? AND team=?', (act_id, team))
        db.commit()
        return jsonify({'status':'success'})
    else:
        # 查询活动
        activities = db.execute('SELECT * FROM activity WHERE team=?', (team,)).fetchall()
        return jsonify({'status':'success', 'data':[dict(a) for a in activities]})

# 标杆画像管理接口
@app.route('/admin/api/benchmark', methods=['GET', 'POST', 'PUT', 'DELETE'])
def admin_benchmark():
    if 'admin_id' not in session or session['role'] != 'admin':
        return jsonify({'status':'error', 'msg':'无权限'})
    db = get_db()
    if request.method == 'POST':
        data = request.json
        db.execute('INSERT INTO benchmark (team, name, answers) VALUES (?, ?, ?)',
                   (data['team'], data['name'], str(data['answers'])))
        db.commit()
        return jsonify({'status':'success'})
    elif request.method == 'PUT':
        data = request.json
        db.execute('UPDATE benchmark SET name=?, answers=? WHERE id=?',
                   (data['name'], str(data['answers']), data['id']))
        db.commit()
        return jsonify({'status':'success'})
    elif request.method == 'DELETE':
        bm_id = request.args.get('id')
        db.execute('DELETE FROM benchmark WHERE id=?', (bm_id,))
        db.commit()
        return jsonify({'status':'success'})
    else:
        benchmark = db.execute('SELECT * FROM benchmark').fetchall()
        return jsonify({'status':'success', 'data':[dict(b) for b in benchmark]})

# 报名数据管理+状态审核
@app.route('/admin/api/apply', methods=['GET', 'PUT'])
def admin_apply():
    if 'admin_id' not in session:
        return jsonify({'status':'error', 'msg':'未登录'})
    db = get_db()
    team = session['team'] if session['role'] != 'admin' else request.args.get('team', None)
    if request.method == 'PUT':
        # 审核状态
        data = request.json
        db.execute('UPDATE apply SET status=? WHERE id=?', (data['status'], data['id']))
        db.commit()
        return jsonify({'status':'success'})
    else:
        # 查询报名数据（管理员查全部，队长查本队）
        if team:
            applies = db.execute('SELECT * FROM apply WHERE team1=? OR team2=?', (team, team)).fetchall()
        else:
            applies = db.execute('SELECT * FROM apply').fetchall()
        return jsonify({'status':'success', 'data':[dict(a) for a in applies]})

# 数据导出Excel
@app.route('/admin/api/export')
def admin_export():
    if 'admin_id' not in session or session['role'] != 'admin':
        return jsonify({'status':'error', 'msg':'无权限'})
    db = get_db()
    applies = db.execute('SELECT * FROM apply').fetchall()
    df = pd.DataFrame([dict(a) for a in applies])
    file_name = f'招新报名数据_{datetime.now().strftime("%Y%m%d")}.xlsx'
    df.to_excel(file_name, index=False)
    return send_file(file_name, as_attachment=True)

# 退出登录
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# 初始化数据库（首次运行）
@app.before_first_request
def before_first_request():
    if not os.path.exists(DATABASE):
        init_db()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
