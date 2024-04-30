# save a value to a cvs file


def save_carbon(carbon, date, hour):
    with open("carbon.csv", "a") as f:
        f.write(date + "," + hour + "," + carbon + "\n")


def find_carbon(date, hour):
    dates = []

    with open("carbon.csv", "r") as f:
        for line in f:
            if date in line and hour in line:
                return line.split(",")[2]
        print("Carbon value not found for that date and hour")
        print("We have the following dates recorded:")
        f.seek(20)
        for line in f:
            if line.split(",")[0] not in dates:
                dates.append(line.split(",")[0])
        for i in dates:
            print(i)
        return None
