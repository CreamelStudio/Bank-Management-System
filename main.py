import csv
import uuid
import os
from enum import Enum
from hashlib import md5
from pathlib import Path

import glob

import pyfiglet
import time
from datetime import datetime

waitSecond = 1

class MenuEnum(Enum):
    MainMenu = 0
    Login = 1
    Register = 2
    Deposit = 3
    Withdraw = 4
    Transaction = 5
    BalanceInquiry = 6
    History = 7
    Exit = 8



loginUUID = None
loginID = None
loginPW = None
loginName = None
currentMenu = MenuEnum.MainMenu

AccountPath = str(Path("data") / "bankAccounts.csv")
ChecksumPath = str(Path("data") / "checksum.csv")

def MainMenu():
    word = pyfiglet.figlet_format("Bank   Management System", font="drpepper")
    print("====================================================================================")
    print(word)
    print("1. 로그인")
    print("2. 회원가입")
    print("3. 입금")
    print("4. 출금")
    print("5. 이체")
    print("6. 잔액 조회")
    print("7. 거래내역 조회")
    print("8. 나가기")
    if loginUUID is not None:
        print(f"{loginName}님, 환영합니다!")
    else:
        print(f"기능을 사용하려면 로그인을 해주세요!")
    print("====================================================================================")

    menuInput = input("Input Menu Number : ")

    #숫자인지 확인
    if menuInput.isdigit():
        selectedMenu = int(menuInput)
    else:
        selectedMenu = -1

    #범위안에 들어오는지 확인
    if selectedMenu >= 1 and selectedMenu <= 8:
        return selectedMenu
    else:
        print("잘못된 번호입니다.")
        ReturnToMain()
        return -1

def ReturnToMain():
    print(f"{waitSecond}초 후 메인메뉴로 돌아갑니다!")
    time.sleep(waitSecond)
    global currentMenu
    currentMenu = MenuEnum.MainMenu

def GetLoginPath(UUID):
    return str(Path("data") / f"{UUID}.csv")


def amountFormater(amount):
    return format(int(amount), ',d')

def GetBalance(rows):
    if rows:
        balance = int(rows[-1]["Balance"])
    else:
        balance = 0

    return balance

def IsLoggedIn():
    if loginUUID is None:
        print("로그인이 되지 않았습니다, 로그인 후 다시 진행해주세요!")
        ReturnToMain()
        return False
    else:
        return True

def printMenuUI():
    word = pyfiglet.figlet_format(currentMenu.name)
    print("====================================================================================")
    print(word)
    print("====================================================================================")

    if currentMenu == currentMenu.Login:
        LoginBank()
    if currentMenu == currentMenu.Register:
        RegisterBank()
    if currentMenu == currentMenu.Deposit:
        DepositBank()
    if currentMenu == currentMenu.Withdraw:
        WithdrawBank()
    if currentMenu == currentMenu.Transaction:
        TransactionBank()
    if currentMenu == currentMenu.BalanceInquiry:
        BalanceInquiryBank()
    if currentMenu == currentMenu.History:
        TransactionHistory()

def RegisterBank():
    bankID = input("Enter Bank ID : ")
    bankPW = input("Enter Bank PW : ")
    bankName = input("Enter Bank Name : ")

    os.makedirs("data", exist_ok=True)

    should_write_header = (
            not os.path.exists(AccountPath)
            or os.path.getsize(AccountPath) == 0
    )

    with open(AccountPath, "a+", newline="") as accounts:
        accounts.seek(0)
        fieldnames = ["bankID", "bankPW", "Name", "UUID"]

        csvreader = csv.DictReader(accounts)
        for row in csvreader:
            if row["bankID"] == bankID:
                print("이미 존재하는 아이디 입니다!")
                ReturnToMain()
                return

        csvwriter = csv.DictWriter(accounts, fieldnames=fieldnames)

        if should_write_header:
            csvwriter.writeheader()

        csvwriter.writerow({
            "bankID": bankID,
            "bankPW": bankPW,
            "Name": bankName,
            "UUID": str(uuid.uuid4())

        })

    print("은행 계좌 등록이 완료되었습니다.\n")

    ReturnToMain()

def LoginBank():
    global loginUUID, loginID, loginName, loginPW
    bankID = input("Enter Bank ID : ")
    bankPW = input("Enter Bank PW : ")

    try:
        with open(AccountPath, 'r', newline='') as accounts:
            accounts.seek(0)
            csvreader = csv.DictReader(accounts)
            for row in csvreader:
                if row["bankID"] == bankID:
                    if row["bankPW"] == bankPW:
                        loginUUID = row['UUID']
                        loginID = row['bankID']
                        loginName = row['Name']
                        loginPW = row['bankPW']
                        print(f"은행 로그인에 성공했습니다. {row['Name']}님 환영합니다!\n")
                        ChecksumTest()


                    else:
                        print("비밀번호가 일치하지 않습니다.")
            if loginUUID is None:
                print("존재하지 않는 계정입니다.")
    except FileNotFoundError:
        print("존재하지 않는 계정입니다.")
    except Exception as e:
        print(f"알 수 없는 오류로 로그인에 실패하였습니다. {e}\n")

    ReturnToMain()

def DepositBank():
    if not IsLoggedIn():
        return

    amount = input("얼마를 입금하실건가요? : ")

    if not amount.isdigit() or int(amount) <= 0:
        print("잘못된 숫자를 입력하셨습니다!")
        ReturnToMain()
        return


    os.makedirs("data", exist_ok=True)

    path = GetLoginPath(loginUUID)

    if ChecksumTest() == False:
        ReturnToMain()
        return

    should_write_header = (
            not os.path.exists(path)
            or os.path.getsize(path) == 0
    )

    with open(path, "a+", newline="") as accountData:
        accountData.seek(0)
        fieldnames = ["Date", "Time", "Type", "Amount", "Balance", "Sender"]

        rows = list(csv.DictReader(accountData))
        balance = GetBalance(rows) + int(amount)

        csvwriter = csv.DictWriter(accountData, fieldnames=fieldnames)

        if should_write_header:
            csvwriter.writeheader()

        csvwriter.writerow({
            "Date": datetime.today().strftime("%Y-%m-%d"),
            "Time": datetime.today().strftime("%H:%M:%S"),
            "Type": "입금",
            "Amount": amount,
            "Balance": balance,
            "Sender": "Bank Management System"
        })

    print(f"{amountFormater(amount)}원, 입금이 완료되었습니다!")
    LogChecksum()
    ReturnToMain()
    return

def WithdrawBank():
    if not IsLoggedIn():
        return

    checkPW = input("비밀번호를 입력해주세요 : ")

    if checkPW != loginPW:
        print("비밀번호가 틀렸습니다!")
        ReturnToMain()
        return

    amount = input("얼마를 출금하실건가요? : ")

    if not amount.isdigit() or int(amount) <= 0:
        print("잘못된 숫자를 입력하셨습니다!")
        ReturnToMain()
        return



    os.makedirs("data", exist_ok=True)

    path = GetLoginPath(loginUUID)

    if ChecksumTest() == False:
        ReturnToMain()
        return

    should_write_header = (
            not os.path.exists(path)
            or os.path.getsize(path) == 0
    )

    with open(path, "a+", newline="") as accountData:
        accountData.seek(0)
        fieldnames = ["Date", "Time", "Type", "Amount", "Balance", "Sender"]

        rows = list(csv.DictReader(accountData))
        balance = GetBalance(rows) - int(amount)

        if balance < 0:
            print("잔액이 부족합니다.")
            ReturnToMain()
            return

        csvwriter = csv.DictWriter(accountData, fieldnames=fieldnames)

        if should_write_header:
            csvwriter.writeheader()

        csvwriter.writerow({
            "Date": datetime.today().strftime("%Y-%m-%d"),
            "Time": datetime.today().strftime("%H:%M:%S"),
            "Type": "출금",
            "Amount": amount,
            "Balance": balance,
            "Sender": "Bank Management System"
        })

    print(f"{amountFormater(amount)}원, 출금이 완료되었습니다!")
    LogChecksum()
    ReturnToMain()
    return

def TransactionBank():
    if not IsLoggedIn():
        return

    checkPW = input("비밀번호를 입력해주세요 : ")

    if checkPW != loginPW:
        print("비밀번호가 틀렸습니다!")
        ReturnToMain()
        return

    sendToID = input("누구에게 이체하실건가요? : ")

    if sendToID == loginID:
        print("본인에게는 이체가 불가능합니다!")
        ReturnToMain()
        return

    with open(AccountPath, "r", newline="") as accounts:
        accounts.seek(0)
        csvreader = csv.DictReader(accounts)

        ReceiverUUID = None
        for row in csvreader:
            if row["bankID"] == sendToID:
                ReceiverUUID = row["UUID"]
                break

        if ReceiverUUID is None:
            print("존재하지 않는 회원입니다.")
            ReturnToMain()
            return

    if ChecksumTest(UUID = ReceiverUUID) == False:
        print("이체 대상의 계좌의 데이터의 변조가 감지되었습니다.")
        ReturnToMain()
        return

    amount = input("얼마를 이체하실건가요? : ")

    if not amount.isdigit() or int(amount) <= 0:
        print("잘못된 숫자를 입력하셨습니다!")
        ReturnToMain()
        return

    os.makedirs("data", exist_ok=True)

    path = GetLoginPath(loginUUID)
    ReceivePath = GetLoginPath(ReceiverUUID)

    if ChecksumTest() == False:
        ReturnToMain()
        return

    should_write_header = (
            not os.path.exists(path)
            or os.path.getsize(path) == 0
    )

    receive_should_write_header = (
            not os.path.exists(ReceivePath)
            or os.path.getsize(ReceivePath) == 0
    )

    with open(path, "a+", newline="") as accountData:
        accountData.seek(0)
        fieldnames = ["Date", "Time", "Type", "Amount", "Balance", "Sender", "Receiver"]

        rows = list(csv.DictReader(accountData))
        balance = GetBalance(rows) - int(amount)

        if balance < 0:
            print("잔액이 부족합니다.")
            ReturnToMain()
            return

        csvwriter = csv.DictWriter(accountData, fieldnames=fieldnames)

        if should_write_header:
            csvwriter.writeheader()

        csvwriter.writerow({
            "Date": datetime.today().strftime("%Y-%m-%d"),
            "Time": datetime.today().strftime("%H:%M:%S"),
            "Type": "출금(이체)",
            "Amount": amount,
            "Balance": balance,
            "Sender": loginID, #출금처
            "Receiver": sendToID #입금처
        })

    with open(ReceivePath, "a+", newline="") as accountData:
        accountData.seek(0)
        fieldnames = ["Date", "Time", "Type", "Amount", "Balance", "Sender", "Receiver"]

        csvreader = csv.DictReader(accountData)
        rows = list(csv.DictReader(accountData))
        balance = GetBalance(rows) + int(amount)

        csvwriter = csv.DictWriter(accountData, fieldnames=fieldnames)

        if receive_should_write_header:
            csvwriter.writeheader()

        csvwriter.writerow({
            "Date": datetime.today().strftime("%Y-%m-%d"),
            "Time": datetime.today().strftime("%H:%M:%S"),
            "Type": "입금(이체)",
            "Amount": amount,
            "Balance": balance,
            "Sender": loginName, #출금처
            "Receiver": sendToID #입금처
        })

    print(f"{sendToID}님에게 {amountFormater(amount)}원을 이체했습니다!")
    LogChecksum()
    ReturnToMain()
    return

def BalanceInquiryBank():
    if not IsLoggedIn():
        return

    path = GetLoginPath(loginUUID)

    if ChecksumTest() == False:
        ReturnToMain()
        return

    try:
        with open(path, "r", newline="") as accountData:
            accountData.seek(0)
            rows = list(csv.DictReader(accountData))
            balance = GetBalance(rows)
    except FileNotFoundError:
        print(f"현재 남은 잔액은 0원 입니다.")
        ReturnToMain()
        return
    except Exception as e:
        print(f"알 수 없는 오류로 조회에 실패하였습니다. {e}\n")
        ReturnToMain()
        return

    print(f"현재 남은 잔액은 {amountFormater(balance)}원 입니다.")
    ReturnToMain()
    return

def TransactionHistory():
    if not IsLoggedIn():
        return

    path = GetLoginPath(loginUUID)

    if ChecksumTest() == False:
        ReturnToMain()
        return

    try:
        with open(path, "r", newline="") as accountData:
            for row in csv.DictReader(accountData):
                print(f"[{row['Date']} {row['Time']}]")
                print(row['Type'])
                if row['Type'] == "입금(이체)" or row['Type'] == "출금(이체)":
                    print(f"입금처 {row['Sender']} | 출금처 {row['Receiver']}")
                print(f"{amountFormater(row['Amount'])}원")
                print(f"잔액 {amountFormater(row['Balance'])}원")
                print("-------------------------------------------")
    except FileNotFoundError:
        print("거래 내역이 없습니다.")
        input("Enter를 누르면 메인화면으로 돌아갑니다.")
        ReturnToMain()
        return
    except Exception as e:
        print(f"알 수 없는 오류로 조회에 실패하였습니다. {e}\n")
        input("Enter를 누르면 메인화면으로 돌아갑니다.")
        ReturnToMain()
        return

    input("Enter를 누르면 메인화면으로 돌아갑니다.")
    ReturnToMain()
    return

def LogChecksum():
    os.makedirs("data", exist_ok=True)

    should_write_header = (
            not os.path.exists(ChecksumPath)
            or os.path.getsize(ChecksumPath) == 0
    )

    with open(ChecksumPath, "w", newline="") as accounts:
        fieldnames = ["FilePath", "Hash"]

        csvwriter = csv.DictWriter(accounts, fieldnames=fieldnames)
        csvwriter.writeheader()



        all_dir = glob.glob(str(Path("data")/"*"), recursive=True)

        for file in all_dir:
            if file == ChecksumPath:
                continue

            hash = md5()

            with open(file, "rb") as f:
                for chunk in iter(lambda: f.read(128 * hash.block_size), b""):
                    hash.update(chunk)

                csvwriter.writerow({
                    "FilePath": file,
                    "Hash": hash.hexdigest()
                })


def ChecksumTest(UUID = None):
    global loginUUID, loginName, loginID, loginPW

    if UUID == None:
        UUID = loginUUID
        print("데이터 위변조 확인중입니다...")

    path = GetLoginPath(UUID)

    if not os.path.exists(path):
        return True

    if not os.path.exists(ChecksumPath):
        print("체크섬 기록이 존재하지 않습니다.")
        return False

    file_hash = md5()

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(128 * file_hash.block_size), b""):
            file_hash.update(chunk)

    calculated_hash = file_hash.hexdigest()

    with open(ChecksumPath, "r", newline="") as checksum_data:
        for row in csv.DictReader(checksum_data):
            if row["FilePath"] == path:
                if row["Hash"] != calculated_hash:
                    if UUID == loginUUID:
                        print("파일 변조가 감지되었습니다. 데이터 삭제 및 로그아웃이 진행됩니다.")
                        loginUUID = None
                        loginName = None
                        loginID = None
                        loginPW = None
                    os.remove(path)
                    return False
                return True

    print("해당 파일의 Checksum 기록을 찾지 못했습니다, 해당 데이터를 삭제합니다.")
    os.remove(path)

    return False







while True:
    selected = MainMenu()
    if selected != -1:
        if MenuEnum(selected) == MenuEnum.Exit:
            break
        currentMenu = MenuEnum(selected)
        printMenuUI()


