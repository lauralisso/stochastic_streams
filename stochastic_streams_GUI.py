# last updated: December 18, 2022
# WBT version 2.2.0

# USE:
# d8 (single grid cell path) stochastic streams model based on DEM 
# brings in random error based on standard deviation distribution of DEM

# INPUTS REQUIRED: DEM file (.TIF, .IMG, .BIL, etc.) & error distribution .txt file
# FINAL OUTPUT: stream location probability raster 

import tkinter as tk
from tkinter import ttk # themed - it will look like a windows/mac application
from tkinter import filedialog
from WBT.whitebox_tools import WhiteboxTools
import os
from numpy import random

class StochasticStreamsModel(tk.Frame): # frame is a box, not a window
    def __init__(self, master=None): #initialization of the pop-up window
        super().__init__(master)
        self.master = master 
        self.pack()
        self.create_widgets()

    def create_widgets(self): # lay out everything
        self.top_frame = ttk.Frame(self)

        padding_x = 15
        padding_y = 9
        self.working_dir = "/" # intialize as top level directory
        
        # Create the DEM input widgets
        self.dem_frame = ttk.Frame(self.top_frame)
        self.dem_label = ttk.Label(self.dem_frame, text="Input DEM file")
        self.dem_label.grid(row=0, column=0, sticky="W") 
        self.dem_string = tk.StringVar() # associated with entry/text box
        self.dem_entry = ttk.Entry(self.dem_frame, width=75, textvariable=self.dem_string)
        self.dem_entry.grid(row=1, column=0)
        self.dem_btn = ttk.Button(self.dem_frame, text="...", command=self.dem_file_selector) #opens file selector when pressing button
        self.dem_btn.grid(row=1, column=1)
        self.dem_frame.grid(row=0, column=0, padx=padding_x, pady=padding_y)

        # Create the number of iterations widget
        self.iteration_frame = ttk.Frame(self.top_frame)
        self.iteration_label = ttk.Label(self.iteration_frame, text="Number of iterations (default = 500)")
        self.iteration_label.grid(row=2, column=0, sticky="W") 
        self.iteration_string = tk.StringVar()
        self.iteration_entry = ttk.Entry(self.iteration_frame, width=75, textvariable=self.iteration_string)
        self.iteration_entry.grid(row=3, column=0)
        self.iteration_frame.grid(row=2, column=0, sticky="W", padx=padding_x, pady=padding_y)

        # Error distribution file widget
        self.error_dist_frame = ttk.Frame(self.top_frame)
        self.error_dist_label = ttk.Label(self.error_dist_frame, text="Error distribution .txt file")
        self.error_dist_label.grid(row=4, column=0, sticky="W") 
        self.error_dist_string = tk.StringVar() 
        self.error_dist_entry = ttk.Entry(self.error_dist_frame, width=75, textvariable=self.error_dist_string)
        self.error_dist_entry.grid(row=5, column=0)
        self.error_dist_btn = ttk.Button(self.error_dist_frame, text="...", command=self.error_dist_file_selector) #opens file selector when pressing button
        self.error_dist_btn.grid(row=5, column=1)
        self.error_dist_frame.grid(row=4, column=0, padx=padding_x, pady=padding_y)

        # Error correlation widget
        self.error_frame = ttk.Frame(self.top_frame)
        self.error_label = ttk.Label(self.error_frame, text="Error autocorrelation in # of grid cells (default = 5.0)")
        self.error_label.grid(row=6, column=0, sticky="W") 
        self.error_string = tk.StringVar() 
        self.error_entry = ttk.Entry(self.error_frame, width=75, textvariable=self.error_string)
        self.error_entry.grid(row=7, column=0)
        self.error_frame.grid(row=6, column=0, sticky="W", padx=padding_x, pady=padding_y)
        
        # Upslope area threshold widget
        self.threshold_frame = ttk.Frame(self.top_frame)
        self.threshold_label = ttk.Label(self.threshold_frame, text="Channel initiation upslope area threshold in # of grid cells (default = 500.0)")
        self.threshold_label.grid(row=8, column=0, sticky="W") 
        self.threshold_string = tk.StringVar() 
        self.threshold_entry = ttk.Entry(self.threshold_frame, width=75, textvariable=self.threshold_string)
        self.threshold_entry.grid(row=9, column=0)
        self.threshold_frame.grid(row=8, column=0, sticky="W", padx=padding_x, pady=padding_y)
        
        # Channel initiation threshold error widget
        self.initiation_frame = ttk.Frame(self.top_frame)
        self.initiation_label = ttk.Label(self.initiation_frame, text="Channel initiation error std. dev. in # of grid cells (default = 100.0)")
        self.initiation_label.grid(row=10, column=0, sticky="W") 
        self.initiation_string = tk.StringVar() 
        self.initiation_entry = ttk.Entry(self.initiation_frame, width=75, textvariable=self.initiation_string)
        self.initiation_entry.grid(row=11, column=0)
        self.initiation_frame.grid(row=10, column=0, sticky="W", padx=padding_x, pady=padding_y)
        
        # Output file widget
        self.output_frame = ttk.Frame(self.top_frame)
        self.output_label = ttk.Label(self.output_frame, text="Output DEM file")
        self.output_label.grid(row=12, column=0, sticky="W") 
        self.output_string = tk.StringVar()
        self.output_entry = ttk.Entry(self.output_frame, width=75, textvariable=self.output_string)
        self.output_entry.grid(row=13, column=0)
        self.output_btn = ttk.Button(self.output_frame, text="...", command=self.output_file_creator) #opens file selector when pressing button
        self.output_btn.grid(row=13, column=1)
        self.output_frame.grid(row=12, column=0, padx=padding_x, pady=padding_y) 

        # Progress bar
        self.pb_frame = ttk.Frame(self.top_frame)

        # progressbar
        self.pb = ttk.Progressbar(
            self.pb_frame,
            orient='horizontal',
            mode='determinate',
            length=280
        )

        # label
        self.pb_value_label = ttk.Label(self.pb_frame, text=self.update_progress_label())
        self.pb_value_label.grid(row=0, column=0, columnspan=1)

        # place the progressbar
        self.pb.grid(row=15, column=1, columnspan=2, padx=padding_x, pady=padding_y)
        self.pb_frame.grid(row=14, column=0, sticky=tk.E, padx=padding_x, pady=padding_y)

        # Okay and Cancel buttons
        self.buttons = ttk.Frame(self.top_frame)
        self.okay = ttk.Button(self.buttons, text="OK", command=self.stochastic_analysis) # run the analysis by calling a function
        self.okay.grid(row=16, column=0)
        self.cancel = ttk.Button(self.buttons, text="Cancel", command=self.master.destroy) # kill the window
        self.cancel.grid(row=16, column=1)
        self.buttons.grid(row=16, column=0, sticky=tk.E, padx=padding_x, pady=padding_y)


        self.top_frame.grid(row=16, column=0)

    def dem_file_selector(self):
        result = self.dem_string.get()
        # opens a file that already exists
        result = filedialog.askopenfilename(initialdir = self.working_dir, title = "Select file", filetypes = (("BIL files","*.bil"),("all files","*.*")))
        self.dem_string.set(result)
        self.working_dir = os.path.dirname(result)

    def error_dist_file_selector(self):
        result = self.error_dist_string.get()
        # opens a file that already exists
        result = filedialog.askopenfilename(initialdir = self.working_dir, title = "Select file", filetypes = (("TXT files","*.txt"),("all files","*.*")))
        self.error_dist_string.set(result)
        self.working_dir = os.path.dirname(result)
    
    def output_file_creator(self):
        result = self.output_string.get()
        # saves output to a new file
        result = filedialog.asksaveasfilename(initialdir = self.working_dir, title = "Select file", filetypes = (("BIL files","*.bil"),("all files","*.*")))
        self.output_string.set(result)
        self.working_dir = os.path.dirname(result)

    def update_progress_label(self):
        return f"Progress: ({self.pb['value']:.1f}%)"

    def progress(self, progress):
        self.pb['value'] = progress
        if self.pb['value'] <= 100:
            self.pb_value_label['text'] = self.update_progress_label()
            self.master.update()   

    def stochastic_analysis(self): # actual flowpath model
        # default parameters
        default_values = (
            "",
            "",
            500,
            "",
            5.0,
            500.0,
            100.0,
            "streams_prob.bil"
        )

        ##########################
        # check for input errors #
        ##########################

        # need a valid path to dem
        dem_file = self.dem_string.get()
        if len(dem_file) == 0:
            print("Invalid DEM file path")

        # check for valid number of iterations (above 0)/set default if blank
        try:
            num_iterations = int(self.iteration_string.get())
        except:
            print("Default value used.")
            num_iterations = default_values[2]
        if num_iterations < 0:
            print("Number of iterations cannot be below 0")

        # check for valid error distribution path       
        error_dist_file = self.error_dist_string.get()
        if len(error_dist_file) == 0:
            print("Invalid error distribution file path")
            
        # check for valid error correlation input (above 0)/set default if blank
        try:
            error_correlation = float(self.error_string.get())
        except:
            error_correlation = 5.0 # default value
            print("Error autocorrelation has been set to the default value of 5.0 grid cells")
            error_correlation = default_values[4]
        if error_correlation < 0:
            print("Error autocorrelation cannot be below 0")
            
        # check for valid upslope area threshold (above 0)/set default if blank
        try:
            upslope_area_threshold = float(self.threshold_string.get())
        except:
            upslope_area_threshold = 500.0 # default value
            print("Channel initiation upslope area threshold has been set to the default value of 500.0 grid cells")
            upslope_area_threshold = default_values[5]
        if upslope_area_threshold < 0.0:
            print("Channel initiation upslope area threshold cannot be below 0")
            
        # check for valid error standard deviation (above 0)/set default if blank
        try:
            initiation_error = float(self.initiation_string.get())
        except:
            num_iterations = 100.0 # default value
            print("Channel initiation error std. dev. has been set to the default value of 100.0 grid cells")
            initiation_error = default_values[6]
        if initiation_error < 0.0:
            print("Channel initiation error std. dev. cannot be below 0")

        # ensure output file name is set, if not use default 
        output_file = self.output_string.get()
        if len(output_file) == 0:
            print(f"Output file has been set to the default name of streams_prob.bil in directory {self.working_dir}")
            output_file = f"{self.working_dir}\{default_values[7]}"
            

        # set-up WhiteboxTools for use
        wbt = WhiteboxTools()
        wbt.set_verbose_mode(False)

        #################
        # Run the model #
        #################

        print("Running model...")

        # create the stream frequency raster by creating a blank raster filled with zeros
        wbt.multiply(
            input1=dem_file, 
            input2="0.0", 
            output="stream_freq.bil"
        )

        old_progress = -1
        for i in range(int(num_iterations)):
            # Generate an error realization
            # Run the RandomField tool
            wbt.random_field(
                base=dem_file, 
                output="random_field.bil"
            )

            # Run the GaussianFilter to add spatial autocorrelation
            wbt.gaussian_filter(
                i="random_field.bil", 
                output="gaussian_filter.bil", 
                sigma=error_correlation
            )
            
            # Run the HistogramMatching tool to force the error field to have the right statistical distribution
            wbt.histogram_matching(
                i="gaussian_filter.bil", 
                histo_file=error_dist_file, 
                output="error_field.bil"
            )

            # Add the error to the DEM
            wbt.add(
                input1="error_field.bil", 
                input2=dem_file, 
                output="error_added_dem.bil"
            )

            # Fill the depressions
            wbt.fill_depressions_wang_and_liu(
                dem="error_added_dem.bil", 
                output="filled_dem.bil", 
                fix_flats=True, 
                flat_increment=None
            )

            # Perform the D8 flow accumulation
            wbt.d8_flow_accumulation(
                i="filled_dem.bil", 
                output="d8_flow_accum.bil", 
                out_type="cells"
            )

            # Threshold for high value (greater than operation)
            if initiation_error > 0.0:
                init_threshold = upslope_area_threshold + random.normal(0.0, initiation_error)
            else:
                init_threshold = upslope_area_threshold

            wbt.greater_than(
                input1="d8_flow_accum.bil", 
                input2=init_threshold, 
                output="streams.bil", 
                incl_equals=True
            )

            # Use the InPlaceAdd tool to add the new streams into our stream frequency raster
            # (updates stream_freq.bil)
            wbt.in_place_add(
                input1="stream_freq.bil", 
                input2="streams.bil"
            )

            progress = int(100.0 * i / num_iterations)
            if progress != old_progress:
                print(f"{progress}%")
                old_progress = progress

        # convert my stream frequency to a stream probability
        # Divide by the number of iterations.
        wbt.divide(
            input1="stream_freq.bil", 
            input2=f"{num_iterations}", 
            output=output_file
        )

        print("Done!")

def main():
    root = tk.Tk() # window that the frame is put on
    root.title("Stochastic Streams Model") # banner at top of application
    app = StochasticStreamsModel(master=root) # stochastic model
    app.mainloop() # run the window

main()