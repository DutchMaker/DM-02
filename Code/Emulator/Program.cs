using System;
using System.Diagnostics;
using Mono.Terminal;
using Terminal.Gui;

namespace Emulator
{
    public class Program
    {
        private static Cpu cpu = new Cpu();

        private static Label labelTest;
        private static Stopwatch sw = Stopwatch.StartNew();

        public static void Main(string[] args)
        {
            Application.Init();

            Application.MainLoop.AddTimeout(TimeSpan.FromMilliseconds(10), UpdateCpuInfo);
            Application.Top.Add(CreateWindow());
            
            Application.Run();
        }

        private static Window CreateWindow()
        {
            var window = new Window("DM-02 Emulator")
            {
                X = 0,
                Y = 0,
                Width = Dim.Fill(),
                Height = Dim.Fill()
            };

            window.Add(new Button("Quit")
            {
                X = 21,
                Y = Pos.Bottom(window) - 4,
                Clicked = () => { Application.Top.Running = false; }
            });

            var run = new Button("Start")
            {
                X = 2,
                Y = Pos.Bottom(window) - 4
            };

            run.Clicked = () => 
            { 
                if (run.Text == "Start")
                {
                    cpu.Run();
                    run.Text = "Stop ";
                }
                else
                {
                    cpu.Stop();
                    run.Text = "Start";
                }
            };

            window.Add(run);

            window.Add(new Button("Reset")
            {
                X = 11,
                Y = Pos.Bottom(window) - 4,
                Clicked = cpu.Reset
            });

            window.FocusLast();

            labelTest = new Label(2, 2, "Test label...");
            window.Add(labelTest);

            return window;
        }

        private static bool UpdateCpuInfo(MainLoop caller)
        {
            labelTest.Text = sw.ElapsedTicks.ToString();
            return true;
        }
    }
}
