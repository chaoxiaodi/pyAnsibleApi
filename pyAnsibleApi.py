import json
import shutil
from ansible.module_utils.common.collections import ImmutableDict
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.plugins.callback import CallbackBase
from ansible import context
import ansible.constants as C


class ResultCallback(CallbackBase):
    """
    重写callbackBase类的部分方法
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.host_ok = {}
        self.host_unreachable = {}
        self.host_failed = {}
        self.task_ok = {}

    def v2_runner_on_unreachable(self, result):
        self.host_unreachable[result._host.get_name()] = result

    def v2_runner_on_ok(self, result, **kwargs):
        self.host_ok[result._host.get_name()] = result

    def v2_runner_on_failed(self, result, **kwargs):
        self.host_failed[result._host.get_name()] = result


class AnsibleApi(object):

    def __init__(self,
                 host_lists=None,
                 iswin=False,  # 是否是windows主机 根据此参数修改部分内容, 如果是windows主机则必须设置用户名和密码
                 port=22,  # 主机 ssh 方式默认管理端口, 如果修改了自定义端口，必须传递此项
                 connection='smart',  # 连接方式 local 本地方式，smart ssh方式 winrm 管理windows的连接方式
                 remote_user=None,  # ssh 用户
                 remote_password=None,  # ssh 用户的密码，应该是一个字典, key 必须是 conn_pass
                 private_key_file=None,  # 指定自定义的私钥地址
                 sudo=None, sudo_user=None, ask_sudo_pass=None,
                 module_path=None,  # 模块路径，可以指定一个自定义模块的路径
                 become=None,  # 是否提权
                 become_method=None,  # 提权方式 默认 sudo 可以是 su
                 become_user=None,  # 提权后，要成为的用户，并非登录用户
                 check=False, diff=False,
                 listhosts=None, listtasks=None, listtags=None,
                 verbosity=3,
                 syntax=None,
                 start_at_task=None,
                 ):

        self.iswin = iswin
        # 如果是 windows 主机 端口修改为 5985, 连接方式修改为 winrm
        if self.iswin:
            port = 5985
            connection = 'winrm'
        # 函数文档注释
        """
        初始化函数，定义的默认的选项值，
        在初始化的时候可以传参，以便覆盖默认选项的值
        """
        context.CLIARGS = ImmutableDict(
            connection=connection,
            remote_user=remote_user,
            private_key_file=private_key_file,
            sudo=sudo,
            sudo_user=sudo_user,
            ask_sudo_pass=ask_sudo_pass,
            module_path=module_path,
            become=become,
            become_method=become_method,
            become_user=become_user,
            verbosity=verbosity,
            listhosts=listhosts,
            listtasks=listtasks,
            listtags=listtags,
            syntax=syntax,
            start_at_task=start_at_task,
        )
        # 实例化数据解析器
        self.loader = DataLoader()

        # 设置密码
        self.passwords = dict(conn_pass=remote_password)

        # 实例化回调插件对象
        self.results_callback = ResultCallback()

        # 三元表达式，假如没有传递 host_lists, 就使用 "localhost,"
        # 指定 host_lists 文件
        # host_lists 的值可以是一个 资产清单文件
        # 也可以是一个包含主机的元组，这个仅仅适用于测试
        #  比如 ： 1.1.1.1,    # 如果只有一个 IP 最后必须有英文的逗号
        #  或者： 1.1.1.1, 2.2.2.2
        self.host_lists = host_lists

        # self.sources = ','.join(host_lists) if host_lists else 'localhost'
        # if len(host_lists) == 1:
        #     self.sources += ','

        # 实例化 资产配置对象
        # 因为要通过动态添加主机修改端口，sources 不能添加原始信息；
        # 如果管理端口默认为 22 可以直接通过sources进行添加
        self.inventory = InventoryManager(loader=self.loader, sources='localhost,')
        for h in host_lists:
            self.inventory.add_host(h, port=port)

        # 变量管理器
        self.variable_manager = VariableManager(self.loader, self.inventory)

    def run(self, args, gether_facts="no", module="shell", task_time=0):
        """
        参数说明：
        task_time -- 执行异步任务时等待的秒数，这个需要大于 0 ，等于 0 的时候不支持异步（默认值）。这个值应该等于执行任务实际耗时时间为好
        """
        if self.iswin:
            module = 'raw'

        play_source = dict(
            name="Ad-hoc",
            hosts=self.host_lists,
            gather_facts=gether_facts,
            tasks=[
                # 这里每个 task 就是这个列表中的一个元素，格式是嵌套的字典
                # 也可以作为参数传递过来，这里就简单化了。
                {"action": {"module": module, "args": args}, "async": task_time, "poll": 0}])

        play = Play().load(play_source, variable_manager=self.variable_manager, loader=self.loader)

        tqm = None
        try:
            tqm = TaskQueueManager(
                inventory=self.inventory,
                variable_manager=self.variable_manager,
                loader=self.loader,
                passwords=self.passwords,
                stdout_callback=self.results_callback)

            result = tqm.run(play)
        finally:
            if tqm is not None:
                tqm.cleanup()
            shutil.rmtree(C.DEFAULT_LOCAL_TMP, True)

    def playbook(self, playbooks):
        """
        Keyword arguments:
        playbooks --  需要是一个列表类型
        """
        from ansible.executor.playbook_executor import PlaybookExecutor

        playbook = PlaybookExecutor(playbooks=playbooks,
                                    inventory=self.inventory,
                                    variable_manager=self.variable_manager,
                                    loader=self.loader,
                                    passwords=self.passwords)

        # 使用回调函数
        playbook._tqm._stdout_callback = self.results_callback

        result = playbook.run()

    def get_result(self):
        result_raw = {'success': {}, 'failed': {}, 'unreachable': {}}

        # print(self.results_callback.host_ok)
        for host, result in self.results_callback.host_ok.items():
            result_raw['success'][host] = result._result
        for host, result in self.results_callback.host_failed.items():
            result_raw['failed'][host] = result._result
        for host, result in self.results_callback.host_unreachable.items():
            result_raw['unreachable'][host] = result._result

        # 最终打印结果，并且使用 JSON 继续格式化
        print(json.dumps(result_raw, indent=4))
