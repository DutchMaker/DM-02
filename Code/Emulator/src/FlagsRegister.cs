namespace Emulator
{
    public class FlagsRegister
    {
        public BusConnections BUS { get; set; }

        public Clock CLOCK { get; set; }

        public bool Load { get; set; }

        public bool Carry { get; set; }

        public bool Overflow { get; set; }

        public bool Zero { get; set; }

        public bool Negative { get; set; }

        public void Tick()
        {
        }
    }
}