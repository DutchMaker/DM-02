namespace Emulator
{
    public enum ClockState
    {
        None,
        CLOCK1_falling,
        CLOCK1_rising,
        CLOCK2_falling,
        CLOCK2_rising
    }

    public class Clock
    {
        public ClockState State { get; set; }

        private long ticks;

        public bool CLOCK1_falling => State == ClockState.CLOCK1_falling;
        public bool CLOCK1_rising => State == ClockState.CLOCK1_rising;
        public bool CLOCK2_falling => State == ClockState.CLOCK2_falling;
        public bool CLOCK2_rising => State == ClockState.CLOCK2_rising;

        public void Tick()
        {
            ticks++;

            switch (ticks)
            {
                case 1:
                    State = ClockState.CLOCK1_rising;
                    break;
                case 3:
                    State = ClockState.CLOCK2_rising;
                    break;
                case 5:
                    State = ClockState.CLOCK1_falling;
                    break;
                case 7:
                    State = ClockState.CLOCK2_falling;
                    break;
                case 8:
                    State = ClockState.None;
                    ticks = 0;
                    break;
                default:
                    State = ClockState.None;
                    break;
            }

        }
    }
}