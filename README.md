# SpaceONE Scenario Test Framework

To run scenario:

`spaceone test [-h] [-d DIR] [-f] [-s SCENARIO] [-c CONFIG] [-p PARAMETERS] [-v VERBOSE]`

Example:

`spaceone test -d ./test/integration/domain`

# Sample

## inventory.ResourceGroup

~~~python
"inventory.ResourceGroup": [
	{"name": "my t3.small servers at ap-northeast-2c",
	 "resources": [{
	 		"resource_type": "inventory.Server",
			"filter": [
				{"k": "data.compute.instance_type", "v": "t3.small", "o": "eq"},
				{"k": "data.compute.az", "v": "ap-northeast-2c", "o": "eq"}
				]
			}
		]
	}
]
~~~
