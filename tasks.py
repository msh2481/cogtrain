import asyncio
import json
import random
from collections import defaultdict
from itertools import combinations
from typing import Callable
import numpy as np
from beartype import beartype as typed
from tqdm import tqdm
from gpt import batch_invoke, invoke
import pylcs


TaskInstance = dict[str, str]
Response = str
Metrics = dict[str, str | float | int | list[str] | list[float] | list[int]]
Info = tuple[
    Callable[[], list[TaskInstance]], Callable[[TaskInstance, list[Response]], Metrics]
]
task_info: dict[str, Info] = {}


@typed
def prepare_IS() -> list[TaskInstance]:
    prompt = """
Please generate 5 examples of insight tasks that could be used in a psychology study. 
Each example is a description of an unusual situation. In the next stage of the test participants will be asked to think of possible causes of these situations.
Provide the output as a JSON array of strings.

Example output:
[
  "A small village that has always been known for its sunny weather and lack of rainfall suddenly experiences a week of non-stop rain, leading to the streets flooding and the villagers being utterly unprepared.",
  "A high school basketball team, which has been losing every game for the entire season, surprisingly wins against the top team in the league by a significant margin.",
  "In a bustling city, a street performer plays music every day and always draws a large crowd. One day, despite playing the same music at the same time and place, no one stops to listen.",
  "A family of four goes to bed at their usual time, but in the morning, they all wake up in a different room of the house, not remembering how they got there.",
  "In a small, tight-knit community, a rumor about a hidden treasure buried somewhere within the town spreads rapidly, inciting a frenzy of digging and searches by the locals."
]
""".strip()
    task_description = "An unusual situation is described below, your task is to think of different causes for the situation."
    while True:
        try:
            response = invoke(prompt, gpt4=(random.random() < 0.5))
            if response.startswith("```json"):
                response = response[7:-3]
            results = json.loads(response)
            assert isinstance(results, list)
            prompted = [{"prompt": task_description + "\n" + task} for task in results]
            return prompted
        except:
            print(f"Error: {response}")


@typed
def grade_originality(task: TaskInstance, responses: list[Response]) -> Metrics:
    k = 5
    gradings: list[list[float]] = [[] for _ in responses]

    prompts = []
    for response in responses:
        prompt = f"""
You are evaluating responses of participants in a creativity training study. 
The task given to them was:
{task["prompt"]}

The response is:
{response}

Please grade its originality on a 0 to 10 scale.
That is, 0 means the most common or trivial answer, 10 is a really imaginative one.
Provide your grade as a single integer, don't print anything else.
""".strip()
        prompts.extend([prompt for _ in range(k)])
    gpt_responses = asyncio.run(batch_invoke(prompts))
    for i in range(len(gpt_responses)):
        try:
            parsed = float(gpt_responses[i].strip())
            gradings[i // k].append(parsed)
        except Exception as e:
            print(e)
            print(gpt_responses[i])
    originality_scores = np.array([sum(a) / len(a) for a in gradings])
    return {
        "fluency": len(responses),
        "mean_originality": (
            0.0 if len(originality_scores) == 0 else originality_scores.mean()
        ),
        "total_originality": originality_scores.sum(),
        "originality_scores": originality_scores.tolist(),
    }


task_info["IS"] = (prepare_IS, grade_originality)


@typed
def prepare_US() -> list[TaskInstance]:
    prompt = """
Please generate 10 examples of weird worlds, which have one major distinction from ours.
Generate only very unique universes, which nobody has thought of before.
Also don't provide too different worlds, they should look similar to ours, except for one local difference.
Provide the output as a JSON array of strings.

Example output:
[
    "A world where all secrets are protected by unbreakable encryption, ensuring privacy and security.",
    "In this reality, the concept of currency does not exist. Instead, all societies operate on a sophisticated barter system, where goods and services are exchanged directly based on mutual agreements.",
    "In a parallel universe, all forms of transportation are based on sophisticated floating technologies. Vehicles, buildings, and even personal movements are powered by anti-gravity devices.",
    "A world where plasma weapons have replaced traditional firearms as the primary means of defense.",
    "Here, plants possess the ability to grow at an accelerated rate, maturing from seedlings to full-grown in just a few days, depending on the species.",
    "In this alternate reality, water behaves as a rare and non-renewable resource due to a unique geological history of the planet.",
    "A world where invisibility cloaks enable individuals to move about undetected.",
    "This parallel world discovered a natural resource that emits a constant, gentle light.",
    "In another universe, the concept of sleep does not exist for any living creature. Instead, beings have evolved to rest and rejuvenate through an hour of complete stillness and silence each day.",
    "Here, the gravitational force of the Earth is half as strong as in our universe.",
]
""".strip()
    task_description = "An utopical situation is described below, your task is to think of interesting consequences from it."
    while True:
        try:
            response = invoke(prompt, gpt4=True, T=1.5)
            if response.startswith("```json"):
                response = response[7:-3]
            results = json.loads(response)
            assert isinstance(results, list)
            prompted = [{"prompt": task_description + "\n" + task} for task in results]
            return prompted
        except:
            print(f"Error: {response}")


task_info["US"] = (prepare_US, grade_originality)


@typed
def prepare_PI() -> list[TaskInstance]:
    prompt = """
Please generate 30 examples of products that might be popular among common people.
Provide the output as a JSON array of strings.

Example output:
[
    "Wireless keyboard",
    "Mechanical pencil",
    "Lava lamp",
    "Trash bags",
    "Reusable water bottle",
    "Electric toothbrush",
    "Laptop backpack",
    "Yoga mat",
    "Comfortable and durable sneakers",
    "Magnifying glass",
    "Bluetooth speakers",
    "Silicone baking mat",
    "Eco-friendly shopping bags",
    "Skincare product",
    "Fitness tracker band",
    "Cotton bed sheet",
    "High-speed HDMI cable",
    "Solar-powered garden light",
    "Memory foam pillow",
    "Reusable silicone food bag",
    "Photo album",
    "Desktop calendar",
    "Biodegradable phone case",
    "Digital kitchen scale",
    "Clip-on book reading light",
    "Desk organizer",
    "Spice rack organizer",
    "Reusable makeup remover pad",
    "Scented candle",
    "MP3 player",
]
""".strip()
    task_description = "For a product given below you need to suggest possible improvements, as many and as original as possible."
    while True:
        try:
            response = invoke(prompt, gpt4=True, T=1.0)
            if response.startswith("```json"):
                response = response[7:-3]
            results = json.loads(response)
            assert isinstance(results, list)
            prompted = [{"prompt": task_description + "\n" + task} for task in results]
            return prompted
        except:
            print(f"Error: {response}")


task_info["PI"] = (prepare_PI, grade_originality)


@typed
def prepare_AU() -> list[TaskInstance]:
    prompt = """
Please generate 30 everyday objects that might have a different application.
Provide the output as a JSON array of strings.

Example output:
[
    "Straws",
    "Sponges",
    "Glass jar",
    "Vinegar",
    "Paper clips",
    "Duct tape",
    "Tea bags",
    "Ruler",
    "Rubber band",
    "Pencil",
]
""".strip()
    task_description = "An everyday object is given below, think of as many possible ways to use it as possible."
    while True:
        try:
            response = invoke(prompt, gpt4=True, T=1.0)
            if response.startswith("```json"):
                response = response[7:-3]
            results = json.loads(response)
            assert isinstance(results, list)
            prompted = [{"prompt": task_description + "\n" + task} for task in results]
            return prompted
        except:
            print(f"Error: {response}")


task_info["AU"] = (prepare_AU, grade_originality)


@typed
def prepare_RAT() -> list[TaskInstance]:
    connections: dict[str, list[str]] = defaultdict(list)
    with open("cue-target.txt", "r", encoding="utf-8") as f:
        for line in f:
            cue, target, fsg = line.strip().split("\t")
            connections[cue].append(target)
    print("Read associations data")
    tasks: list[TaskInstance] = []
    for root, targets in tqdm(connections.items()):
        for comb in combinations(targets, 3):
            tasks.append(
                {
                    "prompt": " ".join(comb),
                    "answer": root,
                }
            )
    random.shuffle(tasks)
    print(tasks[:10])
    return tasks


@typed
def grade_RAT(task: TaskInstance, responses: list[Response]) -> Metrics:
    is_correct = [
        pylcs.edit_distance(response.strip().lower(), task["answer"].lower()) <= 1
        for response in responses
    ]
    return {
        "accuracy": 0 if len(is_correct) == 0 else sum(is_correct) / len(is_correct)
    }


task_info["RAT"] = (prepare_RAT, grade_RAT)


@typed
def prepare_NB() -> list[TaskInstance]:
    return [
        {"prompt": "Practice at https://brainscale.net/app/dual-n-back/training."}
        for _ in range(100)
    ]


@typed
def grade_NB(task: TaskInstance, responses: list[Response]) -> Metrics:
    while True:
        try:
            performance = float(input("Performance (e.g. 2.92): ").strip())
            return {"performance": performance}
        except:
            print("Please enter a number")


task_info["NB"] = (prepare_NB, grade_NB)


@typed
def generate_arithmetic_expression(
    num_operations: int,
    allowed_operations: list[str] = ["+", "-", "*", "//"],
    lam: float = 10,
) -> str:
    """
    Generates an arithmetic expression based on the specified difficulty level.

    Args:
        num_operations (int): The number of operations in the expression.
        allowed_operations (str): A list of allowed arithmetic operations.
        lam (float): The mean for the geometric distribution.

    Returns:
        str: The generated arithmetic expression in infix notation.
    """
    while True:
        remaining_operations = num_operations
        stack: list[str] = []

        while remaining_operations > 0:
            if len(stack) < 2 or (
                len(stack) <= remaining_operations and random.random() < 0.5
            ):
                num = np.random.geometric(p=1 / lam)
                stack.append(str(num))
            else:
                operation = random.choice(allowed_operations)
                first = stack.pop()
                second = stack.pop()
                stack.append(f"({first} {operation} {second})")
                remaining_operations -= 1

        assert len(stack) == 1
        try:
            eval(stack[0])
            return stack[0]
        except:
            continue


@typed
def prepare_MM() -> list[TaskInstance]:
    return [
        {
            "prompt": generate_arithmetic_expression(
                num_operations=np.random.geometric(p=0.5),
                allowed_operations=["+", "-", "*", "//"],
                lam=10.0,
            )
        }
        for _ in range(100)
    ]

@typed
def grade_MM(task: TaskInstance, responses: list[Response]) -> Metrics:
    answer = eval(task["prompt"])
    @typed
    def is_close(response: str) -> bool:
        try:
            number = float(response.strip())
            return abs(number - answer) <= 0.1
        except:
            return False

    correct = [is_close(response) for response in responses]
    return {
        "accuracy": 0 if len(correct) == 0 else sum(correct) / len(correct)
    }