import random
from pcb import PCB


class TaskSimulator:
    """任务调度模拟器"""

    def __init__(self, scheduler):
        self.scheduler = scheduler
        self.current_time = 0
        self.processes = []
        self.execution_history = []  # 格式: [(time, pid, state), ...]
        self.colors = ['#FF5733', '#33FF57', '#5733FF', '#FF33A8',
                       '#33A8FF', '#A8FF33', '#FF8C33', '#8C33FF',
                       '#33FFEC', '#EC33FF', '#FFEC33', '#33ECFF']

    def create_random_processes(self, num_processes, max_burst=20, max_priority=10,
                                max_io_ops=3, max_io_duration=5):
        """创建随机进程"""
        self.processes = []

        for i in range(num_processes):
            # 随机生成进程参数
            burst_time = random.randint(5, max_burst)
            priority = random.randint(1, max_priority)

            # 随机生成I/O操作
            io_times = {}
            num_io = random.randint(0, max_io_ops)
            for _ in range(num_io):
                io_time = random.randint(1, burst_time - 1)
                io_duration = random.randint(1, max_io_duration)
                io_times[io_time] = io_duration

            # 随机到达时间
            arrival_time = random.randint(0, 10)

            # 创建进程
            process = PCB(pid=i + 1, priority=priority, burst_time=burst_time,
                          io_times=io_times, arrival_time=arrival_time)

            # 分配颜色
            process.color = self.colors[i % len(self.colors)]
            self.processes.append(process)

    def create_process(self, pid, priority, burst_time, io_times=None, arrival_time=0):
        """创建指定参数的进程"""
        process = PCB(pid, priority, burst_time, io_times, arrival_time)
        process.color = self.colors[len(self.processes) % len(self.colors)]
        self.processes.append(process)

    def run_simulation(self, max_time=100):
        """运行模拟"""
        self.execution_history = []
        self.current_time = 0

        # 重置所有进程状态
        for process in self.processes:
            process.state = PCB.READY
            process.remaining_time = process.burst_time
            process.executed_time = 0
            process.waiting_time = 0
            process.io_remaining = 0
            process.completion_time = 0
            process.dynamic_priority = process.static_priority
            process.execution_history = []

        # 重置调度器队列
        if hasattr(self.scheduler, 'queues'):  # 多级反馈队列
            self.scheduler.queues = [[] for _ in range(self.scheduler.num_queues)]
            self.scheduler.blocked_queue = []
            self.scheduler.terminated_processes = []
            self.scheduler.current_process = None
            self.scheduler.time_used = 0
            self.scheduler.current_level = 0
        else:  # 其他调度器
            self.scheduler.ready_queue = []
            self.scheduler.blocked_queue = []
            self.scheduler.terminated_processes = []
            if hasattr(self.scheduler, 'current_process'):
                self.scheduler.current_process = None
                self.scheduler.time_used = 0

        # 添加初始到达的进程
        for process in self.processes:
            if process.arrival_time == 0:
                self.scheduler.add_process(process)

        # 主模拟循环
        while self.current_time < max_time:
            # 添加新到达的进程
            for process in self.processes:
                if process.arrival_time == self.current_time and process.state != PCB.READY and process.state != PCB.RUNNING:
                    self.scheduler.add_process(process)

            # 处理I/O完成的进程
            self.scheduler.unblock_processes()

            # 更新等待时间
            self.scheduler.update_queues()

            # 获取下一个执行进程
            current_process = None
            try:
                current_process = self.scheduler.get_next_process()
            except Exception as e:
                print(f"调度器错误: {e}")

            # 执行进程
            if current_process:
                # 确保状态正确
                current_process.state = PCB.RUNNING

                # 执行一个时间单位
                current_process.execute(1)

                # 记录执行历史
                self.execution_history.append((self.current_time, current_process.pid, current_process.state))

                # 更新进程执行历史
                if current_process.execution_history and current_process.execution_history[-1][1] == self.current_time:
                    # 合并连续执行段
                    start_time = current_process.execution_history[-1][0]
                    current_process.execution_history[-1] = (start_time, self.current_time + 1)
                else:
                    current_process.execution_history.append((self.current_time, self.current_time + 1))

                # 检查是否需要I/O
                if current_process.is_io_required(current_process.executed_time):
                    current_process.start_io()
                    self.scheduler.block_process(current_process)

                # 检查进程是否完成
                elif current_process.state == PCB.TERMINATED:
                    self.scheduler.terminate_process(current_process, self.current_time + 1)
            else:
                # 没有进程执行
                self.execution_history.append((self.current_time, None, None))

            # 检查是否所有进程都已完成
            all_terminated = all(p.state == PCB.TERMINATED for p in self.processes)
            if all_terminated:
                break

            # 时间前进
            self.current_time += 1

        return self.execution_history