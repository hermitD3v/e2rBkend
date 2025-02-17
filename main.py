from fastapi import FastAPI, Request, Form, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import csv
from io import StringIO

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def run_script(script_name, *args):
    result = subprocess.run(["sh", script_name, args[0], args[1]], capture_output=True, text=True)
    return result.stdout.strip()

def get_affected_functions():
    subprocess.run(["python", "functionfind.py"],  text=True)


def get_recipe_test():
    result = subprocess.run(["python", "recipetest.py"], capture_output=True, text=True)
    csv_output = result.stdout

    
    testcases = []
    recipes = []
    with open('affected_tests_and_cases_recipe.csv') as csv_file:
    #next(csv_reader, None)
        csv_reader = csv.reader(csv_file)
        for row in csv_reader:
            if len(row)>=3:
                testcases.append(row[1])
                recipes.append(row[2])
    
    return testcases, recipes

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):

    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/run", response_class=HTMLResponse)
def run(request: Request, background_tasks: BackgroundTasks,
              branch_name: str = Form(...), number_of_commits: str = Form(...)):
    
    result = subprocess.run(["sh", "gitPartClone.sh", branch_name, number_of_commits], capture_output=True, text=True)
    print(result)
    result = subprocess.run(["sh", "gitFilesChanged.sh", number_of_commits], capture_output=True, text=True)
    print(result)

    #background_tasks.add_task(run_script, "gitPartClone.sh", branch_name, number_of_commits)
    #background_tasks.add_task(run_script, "gitFilesChanged.sh", branch_name, number_of_commits)

    
    get_affected_functions()

    testcases, recipes = get_recipe_test()
    print(testcases)
    print(recipes)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "testcases": testcases,
        "recipes": recipes
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
