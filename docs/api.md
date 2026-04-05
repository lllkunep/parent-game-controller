# API
### get data
**GET** /api/data  

*Response* JSON  
- **name** string  
- **ip** string  
- **status** enum (ok, have-error)
- **mode** enum (auto, allow, deny) 

## get summary
**GET** /api/summary?date={date}  
*params*
- **date** *optional* string date in SQL format

*Response* JSON  
- **game_time** int, minutes  
- **time_left** int, minutes  
- **unknown_apps_count** int

## get processes
**GET** /api/processes?type={type}  
*params*  
- **type** enum (all, unknown, game, application)  

*Response* JSON  
- **list** list  
  - **id** int
  - **title** string
  - **path** string
  - **type** enum (unknown, game, application)
- **counters** obj
  - **all**
  - **unknown**
  - **game**
  - **application**

## get statistics
**GET** /api/statistics?type={type}&from={from}&to={to}  
*params*  
- **type** enum (all, unknown, game)
- **from** *optional* datetime SQL format
- **to** *optional* datetime SQL format

*Response* JSON  
- **list** list
  - **title** string
  - **path** string
  - **process_id** int
  - **type** enum (unknown, game, application)
  - **total_time** int, minutes
  - **working_time** list
    - **start_time** datetime SQL format
    - **end_time** datetime SQL format

## get options  
**GET** /api/options  

*Response* JSON  
- **usage_limit** time HH:MM
- **time_limits** list
  - **start_time** time HH:MM
  - **end_time** time HH:MM
- **log_interval** int seconds
- **starting_point** time HH:MM

## get logs
**GET** /api/logs?page={page}&from={from}&to={to}  
*params*  
- **page** int
- **from** *optional* datetime SQL format
- **to** *optional* datetime SQL format  

*Response* JSON
- **page** int
- **total_pages** int
- **list** list
  - **time** datetime SQL format
  - **context** string
  - **message** string

## get keywords
**GET** /api/keywords

*Response* JSON
- **keywords** list
  - string

## add keyword
**POST** /api/keywords
*params*
- **keyword** string
- **action** enum (add)

## delete keyword
**POST** /api/keywords
*params*
- **keyword** string
- **action** enum (delete)

## update process
**POST** /api/processes

*params*
- **id** int
- **type** enum (unknown, game, application) 

## update options
**POST** /api/options

*params*
- **name** string
- **value** mixes (time HH:MM, int seconds, string, list)
  - if list, then it must be list of objects with keys:
    - **start_time** time HH:MM
    - **end_time** time HH:MM
