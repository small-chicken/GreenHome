import React from "react";
import './EventSetter.css';

function EventSetter() {
    const appliances = [
      {name: "Washing Machine", runtime_min: 120},
      {name: "Dishwasher", runtime_min: 90},
      {name: "Dryer", runtime_min: 60},
      {name: "Electric Vehicle",runtime_min: 240},
      {name: "Heating System", runtime_min: 180 },
      {name: "Kitchen Appliances",  runtime_min: 45 },
    ]

  const START_OF_DAY = "00:00";
  const END_OF_DAY   = "23:30";
  const dayIndexFromToken = (token) => (token === "tomorrow" ? 1 : 0);
  
  const addDays = (date, days) => {
    const d = new Date(date);
    d.setDate(d.getDate() + days);
    return d;
  };

  const roundUpToSlotHHMM = (d = new Date(), step = 30) => {
  const mins = d.getMinutes();
  const add = (step - (mins % step)) % step;
  d.setMinutes(mins + add, 0, 0);
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  return `${hh}:${mm}`;
};


  const TfromISO = (dayToken, hhmm) => {
  if (!hhmm) return null;
  const [h, m] = hhmm.split(":").map(Number);

  const baseMidnight = new Date();
  baseMidnight.setHours(0, 0, 0, 0);

  const d = addDays(baseMidnight, dayIndexFromToken(dayToken));
  d.setHours(h, m, 0, 0);
  return d.toISOString();
};

  const buildSlots = (start = "00:00", end = "23:30", stepMin = 30) => {
  const toMin = (t) => {
    const [h, m] = t.split(":").map(Number);
    return h * 60 + m;
  };
  const toHHMM = (mins) => {
    const h = String(Math.floor(mins / 60)).padStart(2, "0");
    const m = String(mins % 60).padStart(2, "0");
    return `${h}:${m}`;
  };

  const slots = [];
  for (let t = toMin(start); t <= toMin(end); t += stepMin) {
    slots.push(toHHMM(t));
  }
  return slots;
};

  const dayOptions = [
  { label: "Today",    value: "today" },
  { label: "Tomorrow", value: "tomorrow" },
  ];

   const slots = buildSlots("00:00", "23:30", 30);

   const [open, setOpen] = React.useState(false);
   const [label, setLabel] = React.useState("Choose an appliance");
   const [showTimeOption, setShowTimeOption] = React.useState(false);
   const [timePref, setTimePref] = React.useState(false);
   const [startTime, setStartTime] = React.useState("");      
   const [endTime, setEndTime] = React.useState("");     
   const [startDay, setStartDay] = React.useState(dayOptions[0].value);
   const [endDay, setEndDay] = React.useState(dayOptions[0].value); 
   const [appliance, setAppliance] = React.useState(null);
   const hasEarliest = timePref && !!startTime;
   const hasLatest   = timePref && !!endTime;
   const ref = React.useRef(null);

   React.useEffect(() => {
    const onDocClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)){
        setOpen(false);
      }
    };
    const onKey = (e) => {
      if (e.key === "Escape"){
        setOpen(false);
        setTimeout(() => document.activeElement?.blur(), 0);
      }
    };
    document.addEventListener("click", onDocClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("click", onDocClick);
      document.removeEventListener("keydown", onKey);
    };
    }, []);

  const canSubmit = !!appliance;
  const btnLabel = timePref
  ? hasEarliest && hasLatest
      ? "Add event with time window"
      : hasEarliest
          ? "Add event with earliest start"
          : hasLatest
              ? "Add event with latest end"
              : "Add event"
  : "Add event with no time preferences";


  const handleSubmit = async () => {
  if (!canSubmit || !appliance) return;

  const base = {
    name: appliance.name,
    runtime_min: appliance.runtime_min,
  };

  const payload = timePref
    ? {
        ...base,
        earliest_start: hasEarliest ? TfromISO(startDay, startTime) : null,
        latest_end: hasLatest ? TfromISO(endDay, endTime) : null,
      }
    : {
        ...base,
        earliest_start: null,
        latest_end: null,
      };

  console.log("Submitting event →", payload);

  try {
    const response = await fetch("http://127.0.0.1:8000/scheduler/schedule/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ appliances: [payload] }), // Django expects a list
    });

    const data = await response.json();
    console.log("✅ Scheduler response:", data);

    if (!response.ok) {
      alert(`❌ Error: ${data.error || data.detail || "Unknown error"}`);
    } else {
      alert("✅ Event scheduled successfully!");
    }
  } catch (err) {
    console.error("Request failed:", err);
    alert("⚠️ Failed to contact scheduler backend");
  }
};


    return (
    <div className="event-setter">

      <div
        className={`event-dropdown ${open ? "is-open" : ""}`}
        ref={ref}
      >
        <button
          type="button"
          className="event-dropdown__trigger"
          aria-haspopup="menu"
          aria-expanded={open}
          onClick={(e) => {
            const btn = e.currentTarget; 
            setOpen(prev => {
              const next = !prev;
              if (!next) btn.blur(); 
              return next;
            });
          }}
        >
          {label} ▾
        </button>

        <div className="event-dropdown__menu" role="menu">
          {appliances.map((a) => (
            <button
              key={a.name}
              type="button"
              role="menuitem"
              className="event-dropdown__item"
              onClick={() => {
                setAppliance(a);
                setLabel(a.name);
                setOpen(false);
                setShowTimeOption(true);
              }}
            >
              {a.name}
            </button>
          ))}
        </div>
        
      </div>
      {showTimeOption && (
        <label className="timepref">
          <input
            id="timePref"
            type="checkbox"
            checked={timePref}
            onChange={(e) => setTimePref(e.target.checked)}
          />
          <span>Select time preferences</span>
        </label>
      )}
      {timePref && (
        <div className="timepicker timepicker--range">
          <div className="timefield">
            <label>Earliest Start</label>
            <select
              id="startDay"
              value={startDay}
              onChange={(e) => setStartDay(e.target.value)}
            >
              {dayOptions.map((d) => (
          <option key={d.value} value={d.value}>
            {d.label}
          </option>
        ))}
            </select>

            <select
            id="startTime"
            value={startTime}
            onChange={(e) => setStartTime(e.target.value)}
          >
            <option value="" disabled>Pick a time…</option>
            {slots.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
          </div>
          <div className="timefield">
            <label>Latest End</label>
            <select
              id="endDay"
              value={endDay}
              onChange={(e) => setEndDay(e.target.value)}
            >
              {dayOptions.map((d) => (
                <option key={d.value} value={d.value}>
                  {d.label}
                </option>
              ))}
              </select>

            <select
              id="endTime"
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
            >
              <option value="" disabled>Pick a time…</option>
              {slots.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
          
        </div>
      )}
        <button
          type="button"
          className="event-submit"
          onClick={handleSubmit}
          disabled={!canSubmit}
        >
          {btnLabel}
        </button>
    </div>
  );
}



export default EventSetter