import os

import can
import candas as cd
import matplotlib.pyplot as plt
import pandas as pd


def list_blf_files():
    files = [f for f in os.listdir(".") if f.endswith(".blf")]
    for i, file in enumerate(files, 1):
        print(f"{i}: {file}")
    return files


def read_and_filter(df):
    df = df.astype({df.columns[0]: "float64"})
    df.columns = ["Start Time", "SystemState_xdu8", "SupplyVoltage_xdu16"]
    # Filtering options: uncomment to activate
    # df = df[df['SystemState_xdu8'] != 0]
    # df = df[df['SupplyVoltage_xdu16'] <= 18.0]
    # df = df[df['SupplyVoltage_xdu16'] > 0]
    return df


def add_time_columns(df):
    df["End Time"] = df["Start Time"]
    df["Duration"] = 0.0

    i = 0
    while i < len(df) - 1:
        if df.loc[df.index[i], "SystemState_xdu8"] == df.loc[df.index[i + 1], "SystemState_xdu8"]:
            start_time = df.loc[df.index[i], "Start Time"]
            state = df.loc[df.index[i], "SystemState_xdu8"]
            j = i + 1
            while j < len(df) and df.loc[df.index[j], "SystemState_xdu8"] == state:
                j += 1
            end_time = df.loc[df.index[j - 1], "Start Time"]
            df.loc[df.index[i], "End Time"] = end_time
            df.loc[df.index[i], "Duration"] = end_time - start_time
            df = df.drop(df.index[i + 1 : j]).reset_index(drop=True)
        else:
            i += 1
    return df


def add_off_time_periods(df):
    i = 0
    while i < len(df) - 1:
        gap = df.loc[df.index[i + 1], "Start Time"] - df.loc[df.index[i], "End Time"]
        if gap > 2:
            start_time = df.loc[df.index[i], "End Time"]
            end_time = df.loc[df.index[i + 1], "Start Time"]
            df = pd.concat(
                [
                    df,
                    pd.DataFrame(
                        {
                            "Start Time": [start_time],
                            "End Time": [end_time],
                            "Duration": [end_time - start_time],
                            "SystemState_xdu8": ["Null"],
                            "SupplyVoltage_xdu16": ["Null"],
                        }
                    ),
                ],
                ignore_index=True,
            )
            df = df.sort_values(by="Start Time").reset_index(drop=True)
            i += 1
        i += 1
    return df


def add_cycle_count(result_df):
    cycle_count = 0
    for i in range(len(result_df)):
        if (
            result_df.loc[result_df.index[i], "SystemState_xdu8"] == 5
            and result_df.loc[result_df.index[i], "Duration"] > 800
        ):
            cycle_count += 1
        result_df.loc[result_df.index[i], "Cycle Count"] = cycle_count
    return result_df


def save_picture(df, file_name):
    plt.figure(figsize=(5.1, 1.2))
    plt.axis("off")
    plt.table(cellText=df.values, colLabels=df.columns, cellLoc="center")
    plt.suptitle(file_name, fontsize=10, y=0.45)
    plt.savefig(file_name + ".jpeg", dpi=300, bbox_inches="tight", pad_inches=0.5)
    plt.close()


def save_to_excel(df, file_name):
    file_path = file_name + ".xlsx"
    if os.path.exists(file_path):
        overwrite = input(f"File {file_path} exists. Overwrite? (y/n): ")
        if overwrite.lower() != "y":
            print("File not saved.")
            return
    try:
        df.to_excel(file_path, index=False)
        print(f"Saved to {file_path}")
    except PermissionError:
        print(f"Permission denied: {file_path} is open in another process.")


STATE_LABELS = {
    0: "NULL",
    1: "1: NmWait",
    2: "2: OldKL30Wait",
    3: "3: PreDrive",
    4: "4: DriveDown",
    5: "5: DriveUp",
    6: "6: PostRun",
    7: "7: Off",
    8: "8: Error",
    9: "9: Flash",
    10: "10: LowVolt",
    11: "11",
    12: "12",
    13: "13",
    14: "14",
    15: "15",
}


def main():
    signal_names = ["ID2S09_sApplI_SystemState_xdu8", "ID2S09_uApplI_SupplyVoltage_xdu16"]
    signal_db = cd.load_dbc("dbc")
    previous_cycle_count = 0

    files = list_blf_files()
    if not files:
        print("No BLF files found.")
        return

    for file in files:
        file_name = os.path.splitext(file)[0]
        blf_log = cd.from_file(signal_db, file_name, always_convert=True, verbose=True)
        df = blf_log.to_dataframe(names=signal_names)

        with can.BLFReader(file_name + ".blf") as reader:
            min_timestamp = reader.start_timestamp
            max_timestamp = reader.stop_timestamp
            print(f"Start: {min_timestamp}  Stop: {max_timestamp}")

        df.rename(columns={df.columns[0]: "Time [s]"}, inplace=True)
        df["Time [s]"] = df["Time [s]"].apply(lambda t: f"{t - min_timestamp:.6f}")
        df = pd.concat(
            [df, pd.DataFrame({"Time [s]": [f"{max_timestamp - min_timestamp:.6f}"]})],
            ignore_index=True,
        )

        result = add_time_columns(read_and_filter(df))
        result = add_off_time_periods(result)
        result = result[
            ["SystemState_xdu8", "Duration", "Start Time", "End Time", "SupplyVoltage_xdu16"]
        ]
        result = add_cycle_count(result)
        result["Cycle Count"] += previous_cycle_count
        previous_cycle_count = int(result["Cycle Count"].max())
        result["SystemState_xdu8"] = result["SystemState_xdu8"].map(STATE_LABELS)

        print(result[["SystemState_xdu8", "SupplyVoltage_xdu16", "Start Time", "Duration"]])
        save_picture(result, file_name)
        save_to_excel(result, file_name)


if __name__ == "__main__":
    main()
