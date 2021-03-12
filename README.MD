python 调用 ansible api

### 使用前提：

管理机已经对远程主机进行授权免密登录

代码默认使用root用户以及root用户的默认密钥

管理windows主机需要指定用户名及密码

### 使用示例

#### 管理linux主机

    # 1、linux主机，默认使用密钥登录；远程主机要允许管理机root并正确识别密钥
    # 可以使用ip，可以使用主机名；如果使用主机名要求主机名可以在管理机正确解析
    # 如果使用默认端口22 可以不用指定 port
    # 下面几行代码表示 在两台主机执行 `hostname` 命令
    
    linux_hosts = ['1.1.1.1', 'web.test.com']
    cmd = 'hostname'
    ansible2 = AnsibleApi(host_lists=linux_host, port=22222)
    ansible2.run(args=cmd)
    ansible2.get_result()
    
    返回结果：
    {
    "success": {
        "1.1.1.1": {
            "changed": true,
            "end": "2021-03-12 17:54:59.843614",
            "stdout": "web.test.com",
            "cmd": "hostname",
            "rc": 0,
            "start": "2021-03-12 17:54:59.796905",
            "stderr": "",
            "delta": "0:00:00.046709",
            "invocation": {
                "module_args": {
                    "creates": null,
                    "executable": null,
                    "_uses_shell": true,
                    "strip_empty_ends": true,
                    "_raw_params": "hostname",
                    "removes": null,
                    "argv": null,
                    "warn": true,
                    "chdir": null,
                    "stdin_add_newline": true,
                    "stdin": null
                }
            },
            "stdout_lines": [
                "web.test.com"
            ],
            "stderr_lines": [],
            "ansible_facts": {
                "discovered_interpreter_python": "/usr/bin/python"
            },
            "_ansible_no_log": false
        },
        "web.test.com": {
            "changed": true,
            "end": "2021-03-12 17:55:01.107510",
            "stdout": "web.test.com",
            "cmd": "hostname",
            "rc": 0,
            "start": "2021-03-12 17:55:01.059064",
            "stderr": "",
            "delta": "0:00:00.048446",
            "invocation": {
                "module_args": {
                    "creates": null,
                    "executable": null,
                    "_uses_shell": true,
                    "strip_empty_ends": true,
                    "_raw_params": "hostname",
                    "removes": null,
                    "argv": null,
                    "warn": true,
                    "chdir": null,
                    "stdin_add_newline": true,
                    "stdin": null
                }
            },
            "stdout_lines": [
                "web.test.com"
            ],
            "stderr_lines": [],
            "ansible_facts": {
                "discovered_interpreter_python": "/usr/bin/python"
            },
            "_ansible_no_log": false
        }
    },
    "failed": {},
    "unreachable": {}
    }

#### 管理windows主机

    # 2、 windows主机，默认使用用户名密码登录，需要传递正确的用户名以及密码，和iswin标记
    # 
    win_host = ['2.2.2.2', 'win.test.com']
    cmd = 'hostname'
    user = 'administrator'
    pwd = 'windadminmima'
    ansible2 = AnsibleApi(host_lists=win_host, remote_user=user, remote_password=pwd, iswin=True)
    ansible2.run(args=cmd)
    ansible2.get_result()
    
    返回结果：
    {
    "success": {
        "2.2.2.2": {
            "rc": 0,
            "stdout": "2\r\n",
            "stdout_lines": [
                "2"
            ],
            "stderr": "",
            "stderr_lines": [],
            "changed": true,
            "_ansible_no_log": false
        },
        "win.test.com": {
            "rc": 0,
            "stdout": "win.test.com\r\n",
            "stdout_lines": [
                "win.test.com"
            ],
            "stderr": "",
            "stderr_lines": [],
            "changed": true,
            "_ansible_no_log": false
        }
    },
    "failed": {},
    "unreachable": {}
    }

欢迎各位大佬解锁更多使用方式并反馈~


### 参考 & 感谢
[ansible官网](https://docs.ansible.com/ansible/latest/dev_guide/developing_api.html)

[运维开发_西瓜甜 的简书文章](https://www.jianshu.com/p/ec1e4d8438e9)


