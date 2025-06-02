class PCB:
    """进程控制块 (Process Control Block)"""

    # 进程状态
    READY = "Ready"
    RUNNING = "Running"
    BLOCKED = "Blocked"
    TERMINATED = "Terminated"

    def __init__(self, pid, priority, burst_time, io_times=None, arrival_time=0):
        """
        初始化进程控制块

        Args:
            pid: 进程ID
            priority: 初始优先级 (数字越小，优先级越高)
            burst_time: 总CPU执行时间
            io_times: 字典 {时间点: 持续时间} - 什么时候需要I/O以及需要多长时间
            arrival_time: 进程到达系统的时间
        """
        self.pid = pid
        self.static_priority = priority
        self.dynamic_priority = priority  # 可在执行期间被修改
        self.burst_time = burst_time
        self.remaining_time = burst_time
        self.io_times = io_times or {}
        self.arrival_time = arrival_time
        self.state = PCB.READY
        self.executed_time = 0
        self.waiting_time = 0
        self.io_remaining = 0
        self.completion_time = 0
        self.color = None  # 由模拟器分配，用于可视化
        self.execution_history = []  # 记录进程执行的时间段 [(start_time, end_time), ...]

    def update_dynamic_priority(self, aging_factor=1):
        """根据等待时间更新动态优先级"""
        self.dynamic_priority = max(1, self.static_priority - (self.waiting_time // aging_factor))

    def is_io_required(self, current_time):
        """检查当前时间是否需要I/O操作"""
        return self.executed_time in self.io_times and self.state == PCB.RUNNING

    def start_io(self):
        """开始I/O操作"""
        self.io_remaining = self.io_times[self.executed_time]
        self.state = PCB.BLOCKED

    def update_io(self):
        """更新I/O操作时间"""
        if self.state == PCB.BLOCKED:
            self.io_remaining -= 1
            if self.io_remaining <= 0:
                self.state = PCB.READY

    def execute(self, time_unit=1):
        """执行进程一个时间单位"""
        self.state = PCB.RUNNING
        exec_time = min(time_unit, self.remaining_time)
        self.executed_time += exec_time
        self.remaining_time -= exec_time

        if self.remaining_time <= 0:
            self.state = PCB.TERMINATED

        return exec_time

    def update_waiting(self):
        """更新等待时间"""
        if self.state == PCB.READY:
            self.waiting_time += 1