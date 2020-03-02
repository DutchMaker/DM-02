namespace Emulator
{
    public class Cpu
    {
        private bool running = true;

        public CpuModules Modules { get; } = new CpuModules();

        public long Ticks { get; private set; }

        public void Start()
        {
            running = true;
        }
        
        public void Stop()
        {
            running = false;
        }

        public void Reset()
        {
            Ticks = 0;
        }

        public void Step()
        {

        }

        public void Tick()
        {
            if (!running)
            {
                return;
            }

            Ticks++;
            Modules.Tick();
        }
    }
}