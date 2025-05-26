import React, {useState} from "react";

const Autocomplete = (props) => {
  const {options, name, attrs} = props
  const [search, setSearch] = useState("")
  const [result, setResult] = useState("")

  const validOptions = options.filter(opt => search && opt.label.includes(search))

  const handleChange = (event) => {
    setResult("")
    setSearch(event.target.value)
  }

  const handleSelect = (opt) => {
    setResult(opt.value);
    setSearch("")
  }

  return (
    <div>
      <input
        name={name}
        value={result || search || ""}
        onChange={handleChange}
        {...attrs}
      ></input>
      <div className="list-group">
        {
          validOptions.map(
            opt =>
              <button key={opt.value} type="button" onClick={() => handleSelect(opt)} className="list-group-item list-group-item-action">
                {opt.label}
              </button>
          )
        }
      </div>
    </div>
  )
}

export default Autocomplete