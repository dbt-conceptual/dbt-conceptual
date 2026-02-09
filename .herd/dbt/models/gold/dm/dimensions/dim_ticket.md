{% docs dim_ticket %}
Ticket dimension (Type 2 SCD) - tracks historical changes to ticket attributes

**Grain:** One row per ticket version (Type 2 SCD)
**Source:** h_ticket + s_ticket_base
{% enddocs %}
