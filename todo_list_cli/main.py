from rich import print as rich_print
from rich.text import Text


def prompt(query, type_=None, condn=None):
  if type_ is None:
  	type_ = str

  if condn is None:
  	condn = bool

  MOVE_UP_BY_1_LINE = '\033[1A'
  ERASE_WHOLE_LINE = '\033[2K'
  query_str = MOVE_UP_BY_1_LINE + ERASE_WHOLE_LINE + query

  print()
  while True:
    try:
    	val = type_(input(query_str))
    	if condn(val):
  	  	return val
    except Exception:
    	continue
    except KeyboardInterrupt:
    	exit(1)


class ToDoList:
  def __init__(self):
    self.tasks = []

  def add_task(self, task):
    self.tasks.append({"task": task, "completed": False})
    rich_print(f"[green]Task added:[/] {task}")

  def complete_task(self, task_number):
    if not (0 < task_number <= len(self.tasks)):
    	rich_print('[red]Invalid task number[/]')
    	return

    self.tasks[task_number - 1]['completed'] = True
    rich_print(f"[yellow]Task {task_number} marked as complete[/]")

  def show_tasks(self):
    if not self.tasks:
      rich_print('[red]No tasks in the list.[/]')
      return

    length_of_sno = len(str(len(self.tasks)))

    for i, task in enumerate(self.tasks, 1):
      task_text = task['task']
      if task['completed']:
        task_text = f"[strike]{task_text}[/]"
      rich_print(f"{i:>{length_of_sno}}. {task_text}")


def main():
  todo_list = ToDoList()

  while True:
    print("\nOptions:\n" \
          "1. Add Task\n" \
          "2. Complete a Task\n" \
          "3. View Tasks\n" \
          "4. Exit\n")

    choice = prompt(
      "Choose an option: ", int,
      lambda x: 0 < x <= 4
    )

    if choice == 1:
      task = prompt(
        "Enter the task: ",
        lambda x: x.strip(),
        bool
      )
      todo_list.add_task(task)
    elif choice == 2:
      length = len(todo_list.tasks)
      task_number = prompt(
        f"Enter the task number to complete (1-{length}): ",
        int,
        lambda x: 0 < x <= length
      )
      todo_list.complete_task(task_number)
    elif choice == 3:
      todo_list.show_tasks()
    elif choice == 4:
      print("Exiting the To-Do List app.")
      break


if __name__ == "__main__":
  main()
