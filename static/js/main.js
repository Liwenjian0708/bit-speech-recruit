// 京工演说团招新平台前端交互核心
$(function() {
    // 队长科普页音频播放/暂停功能
    let currentAudio = null;
    $('.captain-card').click(function() {
        const audioSrc = $(this).data('audio');
        const audioWrap = $(this).find('.audio-player');
        // 暂停其他音频，仅播放当前
        if (currentAudio && currentAudio !== audioSrc) {
            $('audio').each(function() {
                this.pause();
                this.currentTime = 0;
            });
        }
        // 渲染音频播放器
        audioWrap.html(`<audio src="${audioSrc}" controls autoplay style="width:100%;margin-top:10px;">您的浏览器不支持音频播放`);
        currentAudio = audioSrc;
    });

    // 20道测评题逐页作答逻辑（未选答案无法下一题）
    let currentQ = 1;
    const totalQ = 20;
    // 初始化：隐藏所有题目，显示第一题
    $('.question').hide();
    $(`#q${currentQ}`).show();
    // 下一题按钮
    $('.next-btn').click(function() {
        const hasSelected = $(`#q${currentQ} input:checked`).length > 0;
        if (!hasSelected) {
            alert('请选择一个答案后再继续哦～');
            return;
        }
        if (currentQ < totalQ) {
            $(`#q${currentQ}`).hide();
            currentQ++;
            $(`#q${currentQ}`).show();
            // 滚动到题目顶部，适配移动端
            $('html, body').animate({scrollTop: $('#question-box').offset().top - 80}, 300);
        } else {
            // 最后一题，提交测评答案
            submitTestAnswers();
        }
    });
    // 上一题按钮
    $('.prev-btn').click(function() {
        if (currentQ > 1) {
            $(`#q${currentQ}`).hide();
            currentQ--;
            $(`#q${currentQ}`).show();
            $('html, body').animate({scrollTop: $('#question-box').offset().top - 80}, 300);
        }
    });

    // 提交测评答案到后端，生成匹配报告
    function submitTestAnswers() {
        const answers = {};
        // 收集所有题目的答案
        for (let i = 1; i <= totalQ; i++) {
            answers[i] = $(`#q${i} input:checked`).val() || '';
        }
        // 显示加载动画
        $('#loading-mask').show();
        // 接口请求
        $.ajax({
            url: '/test',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(answers),
            success: function(res) {
                $('#loading-mask').hide();
                if (res.status === 'success') {
                    window.location.href = res.url; // 跳转到匹配报告页
                } else {
                    alert('测评提交失败，请刷新页面重试～');
                }
            },
            error: function() {
                $('#loading-mask').hide();
                alert('网络出错啦，检查网络后重试～');
            }
        });
    }

    // 注册/登录表单切换（无刷新）
    $('#login-tab').click(function() {
        $('#login-form').show();
        $('#register-form').hide();
        $(this).addClass('active');
        $('#register-tab').removeClass('active');
    });
    $('#register-tab').click(function() {
        $('#register-form').show();
        $('#login-form').hide();
        $(this).addClass('active');
        $('#login-tab').removeClass('active');
    });

    // 注册/登录表单提交验证（必填项校验）
    $('.register-submit').click(function() {
        const phone = $('#reg-phone').val().trim();
        const pwd = $('#reg-pwd').val().trim();
        const name = $('#reg-name').val().trim();
        // 简单校验
        if (!phone || !/^1[3-9]\d{9}$/.test(phone)) {
            alert('请填写正确的手机号～');
            return;
        }
        if (!pwd || pwd.length < 6) {
            alert('密码至少6位哦～');
            return;
        }
        if (!name) {
            alert('请填写真实姓名～');
            return;
        }
        $('#register-form').submit();
    });
    $('.login-submit').click(function() {
        const phone = $('#log-phone').val().trim();
        const pwd = $('#log-pwd').val().trim();
        if (!phone || !pwd) {
            alert('手机号和密码不能为空～');
            return;
        }
        $('#login-form').submit();
    });

    // 报名表单提交验证（志愿选择校验）
    $('.apply-submit').click(function() {
        const firstTeam = $('#first-vol').val();
        if (!firstTeam) {
            alert('请选择第一志愿队伍～');
            return;
        }
        $('#apply-form').submit();
    });

    // 后台管理通用交互：增删改查（管理员/队长端）
    // 新增按钮
    $('.add-btn').click(function() {
        $('#add-modal').modal('show');
    });
    // 编辑按钮：回显数据
    $('.edit-btn').click(function() {
        const id = $(this).data('id');
        const apiUrl = $(this).data('url');
        $.ajax({
            url: `${apiUrl}?id=${id}`,
            type: 'GET',
            success: function(res) {
                if (res.status === 'success') {
                    const data = res.data;
                    // 回显数据到编辑表单
                    for (let key in data) {
                        $(`#edit-${key}`).val(data[key] || '');
                    }
                    $(`#edit-id`).val(id);
                    $('#edit-modal').modal('show');
                }
            }
        });
    });
    // 删除按钮：确认删除
    $('.del-btn').click(function() {
        if (!confirm('确定要删除该数据吗？删除后不可恢复～')) {
            return;
        }
        const id = $(this).data('id');
        const apiUrl = $(this).data('url');
        $.ajax({
            url: `${apiUrl}?id=${id}`,
            type: 'DELETE',
            success: function(res) {
                if (res.status === 'success') {
                    window.location.reload(); // 刷新页面
                } else {
                    alert('删除失败，请重试～');
                }
            }
        });
    });
    // 提交新增/编辑数据
    $('.submit-add').click(function() {
        const formData = getFormData('#add-form');
        const apiUrl = $(this).data('url');
        submitAdminData(apiUrl, 'POST', formData, '#add-modal');
    });
    $('.submit-edit').click(function() {
        const formData = getFormData('#edit-form');
        const apiUrl = $(this).data('url');
        submitAdminData(apiUrl, 'PUT', formData, '#edit-modal');
    });
    // 提取表单数据通用方法
    function getFormData(formId) {
        const data = {};
        $(formId).serializeArray().forEach(item => {
            data[item.name] = item.value.trim();
        });
        return data;
    }
    // 提交后台数据通用方法
    function submitAdminData(url, type, data, modalId) {
        $.ajax({
            url: url,
            type: type,
            contentType: 'application/json',
            data: JSON.stringify(data),
            success: function(res) {
                if (res.status === 'success') {
                    $(modalId).modal('hide');
                    window.location.reload();
                } else {
                    alert('操作失败，请重试～');
                }
            }
        });
    }
});

// 通用工具：时间戳格式化（后台数据展示用）
function formatTime(timestamp) {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    const y = date.getFullYear();
    const m = (date.getMonth() + 1).toString().padStart(2, '0');
    const d = date.getDate().toString().padStart(2, '0');
    const h = date.getHours().toString().padStart(2, '0');
    const min = date.getMinutes().toString().padStart(2, '0');
    return `${y}-${m}-${d} ${h}:${min}`;
}

// 页面加载完成后隐藏加载层
$(window).on('load', function() {
    $('#page-loading').hide();
});