# Internal engineering wiki export - Marta Kovacs

## Falcon streaming rebuild
Status: running in production since 03/2025. Replaced the legacy nightly batch with a Kafka
streaming pipeline. Stack: Kafka, Flink, PostgreSQL. Marta was tech lead and wrote the Flink jobs.

## Realtime pricing feed
Status: proposal only. A design document exists for a realtime pricing feed; no implementation.

## Vendor cost dashboard
Status: implemented 2024. Metabase dashboard over the warehouse tracking vendor spend.
Note: the wiki page is authored by another engineer (Peter Szabo) and ownership is unclear.

## Data quality framework
Status: in validation. Great Expectations based checks wired into Airflow. Marta designed it.

## Warehouse migration to Snowflake
Status: proposed for 2027 budget cycle. Not started.
