# vitopy

Retrieve register values from a Viessmann central heating system via OptoLink interface.

## Concept

Use vitopy to read current operating parameters from your Viessmann central heating system.
Contrary to existing tools like vcontrold, vitopy takes a no-frills bare-bones approach:

 * vitopy does not know nor care about what the registers actually mean. It simply reads and stores values. The interpretation of these values is up to a processing tool further down the pipeline.
 * This simplicity makes it straightforward to log many values, and interpret them afterwards. No need to set up complicated round-robin databases and plotting commands right away, before you even know which values are of most interest to you!

## Operation

Call vitopy.py periodically, for example from your crontab.

Details and configuration options to follow. Currently still hard-coded.

## Thanks

Inspired by and based on a lot of groundwork that was done by the people at https://openv.wikispaces.com/.

Thanks to everybody at Viessmann for making their heating systems accessible for third-party tools via their OptoLink interface.
