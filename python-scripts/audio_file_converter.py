import os
import subprocess

def convert_files(input_folder, output_folder):
    # Ensure the output folder exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Iterate over all files in the input folder
    for filename in os.listdir(input_folder):
        input_path = os.path.join(input_folder, filename)

        # Check if the file is a valid file (not a directory)
        if os.path.isfile(input_path):
            # Define the output path
            output_filename = os.path.splitext(filename)[0] + "-converted.wav"
            output_path = os.path.join(output_folder, output_filename)

            # Execute the ffmpeg command to convert the file
            command = [
                "ffmpeg",
                "-i", input_path,
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", "44100",
                output_path
            ]

            try:
                subprocess.run(command, check=True)
                print(f"Successfully converted {input_path} to {output_path}")
            except subprocess.CalledProcessError as e:
                print(f"Error converting {input_path}: {e}")

if __name__ == "__main__":
    input_folder = ""
    output_folder = ""

    convert_files(input_folder, output_folder)
