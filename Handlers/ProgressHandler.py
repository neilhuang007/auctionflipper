from tqdm import tqdm

pbar = None

def createpbar(totalauction):
    global pbar
    pbar = tqdm(total=totalauction, desc="Processing all auctions")

def updatepbar(amount):
    pbar.update(1);