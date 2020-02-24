using System;
using System.Diagnostics;
using Mono.Terminal;
using Terminal.Gui;

namespace Emulator
{
    public class Program
    {
        private const int TICK_INTERVAL = 500;

        private static Cpu cpu = new Cpu();

        private static Label labelTicks;

        private static Label labelClockState;

        public static void Main(string[] args)
        {
            Application.Init();

            Application.MainLoop.AddTimeout(TimeSpan.FromMilliseconds(TICK_INTERVAL), PerformCpuTick);
            Application.MainLoop.AddTimeout(TimeSpan.FromMilliseconds(20), UpdateCpuInfo);
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
                X = 31,
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
                    cpu.Start();
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
                X = 12,
                Y = Pos.Bottom(window) - 4,
                Clicked = cpu.Reset
            });

            window.Add(new Button("Step")
            {
                X = 22,
                Y = Pos.Bottom(window) - 4,
                Clicked = cpu.Step
            });

            labelTicks = new Label(2, 2, "Clock ticks: -");
            labelClockState = new Label(2, 3, "Clock state: -");

            window.Add(labelTicks);
            window.Add(labelClockState);

            return window;
        }

        private static bool UpdateCpuInfo(MainLoop caller)
        {
            labelTicks.Text = $"Clock ticks: {cpu.Ticks}";
            labelClockState.Text = $"Clock state: {cpu.Modules.CLOCK.State.ToString().PadRight(14, ' ')}";

            return true;
        }

        private static bool PerformCpuTick(MainLoop caller)
        {
            cpu.Tick();
            return true;
        }
    }
}
