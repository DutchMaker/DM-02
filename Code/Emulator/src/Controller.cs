namespace Emulator
{
    public class Controller
    {
        public ControlLines ControlLines { get; } = new ControlLines();

        public Clock CLOCK { get; set; }

        public void Tick()
        {
        }
    }
}