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
    # Run the test case script
    subprocess.run(["python", "Testandtestcase.py"], capture_output=True, text=True)

    # Run the recipe script
    subprocess.run(["python", "Recipe.py"], capture_output=True, text=True)

    # Read test cases from the test case output file
    testcases = []
    with open('test_case_names.txt', 'r') as test_file:
        for line in test_file:
            line = line.strip()
            if line:  # Add non-empty lines
                testcases.append(line)

    # Read recipes from the recipe output file
    recipes = []
    with open('recipe.txt', 'r') as recipe_file:
        for line in recipe_file:
            line = line.strip()
            if line:  # Add non-empty lines
                recipes.append(line)

    return testcases, recipes

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):

    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/run", response_class=HTMLResponse)
def run(request: Request, background_tasks: BackgroundTasks,
              branch_name: str = Form(...), number_of_commits: str = Form(...)):
    print("Clicked on run")
    #git clone
    result = subprocess.run(["sh", "gitPartClone.sh", branch_name, number_of_commits], capture_output=True, text=True)
    print(result)
    #git changed functions
    result = subprocess.run(["sh", "gitFilesChanged.sh", number_of_commits], capture_output=True, text=True)
    print(result)

    #get test case and recipe
    get_affected_functions()
    subprocess.Popen('.\PartRepo\HDMTOS\Validation\iVal\BuildScripts\BuildTPLFiles.bat')

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
