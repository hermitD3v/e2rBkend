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
    result = subprocess.run(["sh", script_name, *args], capture_output=True, text=True)
    return result.stdout.strip()

def get_affected_functions():
    subprocess.run(["python", "functionfind.py"], capture_output=True, text=True)

def get_recipe_test():
    result = subprocess.run(["python", "recipetest.py"], capture_output=True, text=True)
    csv_output = result.stdout

    csv_reader = csv.reader(StringIO(csv_output))
    testcases = []
    recipes = []

    next(csv_reader) 

    for row in csv_reader:
        testcases.append(row[1])
        recipes.append(row[2])

    return testcases, recipes

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):

    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/run", response_class=HTMLResponse)
async def run(request: Request, background_tasks: BackgroundTasks,
              branch_name: str = Form(...), number_of_commits: str = Form(...)):
    
    background_tasks.add_task(run_script, "gitPartClone.sh", branch_name, number_of_commits)
    background_tasks.add_task(run_script, "gitFilesChanged.sh", branch_name, number_of_commits)

    
    get_affected_functions()

    testcases, recipes = get_recipe_test()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "testcases": testcases,
        "recipes": recipes
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
