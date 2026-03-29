# Supply Chain & Logistics Industry Crash Course
*Business Models & Technology Focus*

---

## 1. Supply Chain Fundamentals

### Core Concept: Moving Goods from Source to Consumer
Supply chain = network of organizations, activities, resources involved in creating and delivering products. Logistics = physical movement and storage component.

**The flow:** Raw materials → Manufacturing → Distribution → Retail → Consumer

### Key Components

| Component | What it does | Key activities |
|-----------|--------------|----------------|
| **Sourcing/Procurement** | Acquire materials and services | Supplier selection, contracts, purchasing |
| **Manufacturing** | Transform inputs to products | Production planning, quality control |
| **Warehousing** | Store and stage inventory | Receiving, put-away, picking, packing |
| **Transportation** | Move goods between locations | Carrier selection, routing, tracking |
| **Last-mile delivery** | Final leg to consumer | Parcel delivery, local distribution |
| **Returns/Reverse logistics** | Handle returns and recycling | RMA processing, refurbishment |

---

## 2. Value Chain & Key Players

### Transportation Providers

| Mode | Use case | Examples |
|------|----------|----------|
| **Trucking (TL)** | Full container loads | JB Hunt, Schneider, Werner |
| **Trucking (LTL)** | Partial loads, consolidated | FedEx Freight, XPO, Old Dominion |
| **Rail** | Long-haul bulk/heavy goods | Union Pacific, BNSF, CSX |
| **Ocean** | International shipping | Maersk, MSC, CMA CGM |
| **Air freight** | High-value, time-sensitive | FedEx, UPS, DHL |
| **Parcel** | Small packages, B2C/B2B | UPS, FedEx, USPS, Amazon |

### Logistics Service Providers

| Type | Role | Examples |
|------|------|----------|
| **3PL** | Outsourced logistics (warehouse, transport) | DHL Supply Chain, XPO, Ryder |
| **4PL** | Manage entire supply chain (asset-light) | Accenture, CH Robinson |
| **Freight forwarders** | Arrange international shipping | Kuehne+Nagel, DB Schenker, Expeditors |
| **Freight brokers** | Match shippers with carriers | C.H. Robinson, Echo, Coyote |
| **Customs brokers** | Handle import/export compliance | Livingston, Flexport |

### Infrastructure

- **Ports:** LA/Long Beach, Savannah, Rotterdam, Singapore
- **Airports:** Memphis (FedEx hub), Louisville (UPS), Hong Kong
- **Distribution centers:** Owned by retailers, 3PLs, brands
- **Intermodal facilities:** Rail-truck transfer points

### Technology Providers
- TMS vendors (transportation management)
- WMS vendors (warehouse management)
- Visibility platforms
- Freight marketplaces

---

## 3. Business Model Deep Dive

### Asset-Based vs Asset-Light

| Model | Description | Examples |
|-------|-------------|----------|
| **Asset-based** | Own trucks, warehouses, planes | UPS, FedEx, JB Hunt |
| **Asset-light** | Broker/platform, use others' assets | Uber Freight, C.H. Robinson, Flexport |
| **Hybrid** | Some owned, some contracted | XPO, Amazon |

**Tradeoffs:**
- Asset-based: Capital intensive, more control, capacity guarantee
- Asset-light: Lower capex, scalable, margin compression risk

### Transportation Economics

**Trucking:**
```
Revenue = Miles × Rate per Mile
Cost = Driver + Fuel + Equipment + Insurance + Maintenance
```

Key metrics:
- Revenue per mile ($2-4 typical)
- Operating ratio (expenses/revenue, <90% is good)
- Deadhead % (empty miles)
- Driver turnover

**Ocean shipping:**
- Container rates (per TEU or FEU)
- Spot vs contract rates
- Fuel surcharges (BAF)
- Port charges, documentation fees

### Warehousing Economics

**Cost structure:**
- Storage: Per pallet per month
- Handling: Per unit in/out
- Labor: Pick, pack, ship
- Value-added services: Kitting, labeling, returns

**Key metrics:**
- Cost per order
- Orders per labor hour
- Inventory turns
- Fill rate
- Perfect order rate

### Brokerage Economics

```
Gross Margin = Customer Rate - Carrier Rate
Net Margin = Gross Margin - Operating Costs
```

Typical gross margin: 10-20%
Key: Volume, carrier relationships, technology for efficiency

---

## 4. Supply Chain Technology Stack

### Core Systems

| System | Function | Key vendors |
|--------|----------|-------------|
| **TMS** | Transportation planning, execution | Blue Yonder, Oracle, SAP, MercuryGate |
| **WMS** | Warehouse operations | Manhattan, Blue Yonder, SAP EWM |
| **OMS** | Order management | Manhattan, IBM Sterling, Fluent Commerce |
| **ERP** | Enterprise resource planning | SAP, Oracle, Microsoft Dynamics |
| **Procurement** | Sourcing, purchasing | Coupa, SAP Ariba, Jaggaer |

### Transportation Technology

- **Route optimization:** ORTEC, Descartes
- **Fleet management/telematics:** Samsara, Geotab, KeepTruckin
- **Freight matching/marketplaces:** Uber Freight, Convoy, Transfix
- **Visibility:** Project44, FourKites, Descartes MacroPoint
- **Digital freight forwarding:** Flexport, Forto, Freightos

### Warehouse Technology

- **WCS (Warehouse Control):** Controls automation equipment
- **WES (Warehouse Execution):** Orchestrates work
- **Robotics:** Locus, 6 River Systems, Berkshire Grey
- **Pick-to-light/voice:** Lightning Pick, Honeywell Vocollect
- **Autonomous vehicles:** Waymo Via, TuSimple, Plus.ai

### Supply Chain Planning

- **Demand planning:** Anaplan, Blue Yonder, o9 Solutions
- **Inventory optimization:** E2open, Kinaxis, Blue Yonder
- **S&OP (Sales & Operations Planning):** Anaplan, Kinaxis
- **Network design:** LLamasoft (Coupa), Optilogic

### Data & Integration

- **EDI:** X12, EDIFACT standards
- **APIs:** REST APIs for modern integration
- **IoT/sensors:** Temperature, location, shock monitoring
- **Blockchain:** TradeLens (discontinued), FoodTrust

---

## 5. Supply Chain Tech Landscape

### Category Overview

| Category | Description | Examples |
|----------|-------------|----------|
| **Digital freight** | Tech-enabled brokerage/matching | Flexport, Convoy, Uber Freight |
| **Visibility** | Real-time shipment tracking | Project44, FourKites |
| **Warehouse robotics** | Automation for fulfillment | Locus, 6 River, Berkshire Grey |
| **Last-mile** | Final delivery solutions | DoorDash Drive, Veho, Bringg |
| **Procurement** | Sourcing and spend management | Coupa, Zip, Fairmarkit |
| **Planning/AI** | Demand, inventory, network | o9 Solutions, Kinaxis |

### Business Models

| Model | Description | Examples |
|-------|-------------|----------|
| **SaaS platform** | Software subscription | Project44, Coupa |
| **Transaction-based** | Revenue per shipment | Flexport, Uber Freight |
| **RaaS** | Robots-as-a-Service (per pick/hour) | Locus Robotics |
| **Asset-light brokerage** | Margin on freight movement | Convoy, Transfix |

### Notable Companies

| Company | Category | Approach |
|---------|----------|----------|
| Flexport | Digital forwarder | Full-service, tech-enabled |
| Project44 | Visibility | Real-time tracking platform |
| Convoy | Digital trucking | AI-powered freight matching |
| Locus Robotics | Warehouse robots | AMRs for picking |
| o9 Solutions | Planning | AI-powered S&OP |
| Coupa | Procurement | BSM (Business Spend Management) |

---

## 6. Emerging Models & Trends

### AI/ML Applications

**Demand forecasting:**
- ML models using external signals
- Reduce bullwhip effect
- Improve inventory positioning

**Route optimization:**
- Dynamic routing with real-time data
- Multi-constraint optimization
- Autonomous vehicle planning

**Warehouse:**
- Slotting optimization
- Pick path optimization
- Labor planning

**Pricing:**
- Dynamic freight pricing
- Spot rate prediction
- Contract optimization

### Autonomous Vehicles
- **Long-haul trucking:** TuSimple, Plus.ai, Aurora
- **Middle-mile:** Waymo Via, Gatik
- **Last-mile:** Nuro, Starship
- Timeline: Middle-mile happening now, long-haul 2-5 years

### Micro-fulfillment
- Small automated facilities close to customers
- 10-15K sqft vs 1M+ sqft traditional DC
- Enables same-day/next-day delivery
- Players: Fabric, Attabotics, AutoStore

### Sustainability
- Electric vehicles for delivery
- Alternative fuels (hydrogen, LNG)
- Carbon tracking and offsetting
- Circular economy / reverse logistics

### Supply Chain Resilience
- Post-COVID focus on visibility
- Nearshoring/reshoring trend
- Multi-sourcing strategies
- Digital twins for scenario planning

---

## 7. Market Dynamics

### Market Size
- Global logistics: ~$10T
- US trucking: ~$900B
- US parcel: ~$150B
- US warehousing: ~$200B
- Ocean shipping: ~$200B

### Industry Structure

**Fragmented trucking:**
- 90% of carriers have <6 trucks
- Top 10 TL carriers: <10% market share
- Creates opportunity for brokers/platforms

**Consolidated parcel:**
- UPS, FedEx, USPS dominate US
- Amazon building parallel network
- Regional carriers growing

**Ocean oligopoly:**
- Top 10 carriers: ~85% capacity
- Alliance structures
- Rate volatility

### Key Challenges

**Labor:**
- Driver shortage (US short ~80K drivers)
- Warehouse labor competition (Amazon effect)
- Immigration policy impacts

**Cost pressures:**
- Fuel volatility
- E-commerce delivery expectations
- Real estate costs for urban fulfillment

**Technology:**
- Legacy system modernization
- Integration complexity
- Data standardization

**Geopolitical:**
- Trade policy uncertainty
- Port congestion
- Regional conflicts

### Regulatory Environment
- Hours of Service (HOS) for drivers
- ELD mandate (electronic logging)
- FMCSA safety ratings
- Customs/trade compliance
- Environmental regulations

---

## 8. Key Terminology Glossary

| Term | Definition |
|------|------------|
| **3PL/4PL** | Third/Fourth-party logistics provider |
| **TL** | Truckload - full truck shipments |
| **LTL** | Less-than-truckload - consolidated shipments |
| **TEU** | Twenty-foot Equivalent Unit (container measure) |
| **FEU** | Forty-foot Equivalent Unit |
| **Drayage** | Short-haul trucking (usually port/rail) |
| **Intermodal** | Using multiple transport modes |
| **Cross-dock** | Transfer facility without long-term storage |
| **DC/FC** | Distribution Center / Fulfillment Center |
| **SKU** | Stock Keeping Unit |
| **BOL** | Bill of Lading |
| **POD** | Proof of Delivery |
| **ASN** | Advance Ship Notice |
| **EDI** | Electronic Data Interchange |
| **OTIF** | On-Time In-Full (delivery metric) |
| **Fill rate** | % of orders fulfilled from stock |
| **Dwell time** | Time cargo sits at location |
| **Deadhead** | Empty miles (no revenue) |
| **Backhaul** | Return trip with cargo |
| **Lane** | Origin-destination route |
| **Spot rate** | One-time market rate |
| **Contract rate** | Negotiated rate for committed volume |
| **Accessorial** | Additional charges (detention, lumper) |
| **Detention** | Charge for holding equipment |
| **Lumper** | Third-party unloading service |
| **Drop trailer** | Leave trailer for loading/unloading |
| **Live load/unload** | Driver waits during loading |
| **Palletize** | Stack goods on pallets |
| **Pick, pack, ship** | Order fulfillment process |
| **Put-away** | Storing received goods |
| **Slotting** | Optimizing warehouse item placement |
| **Wave** | Batch of orders released for picking |
| **Zone picking** | Workers pick from assigned areas |
| **AMR** | Autonomous Mobile Robot |
| **AGV** | Automated Guided Vehicle |
| **WMS** | Warehouse Management System |
| **TMS** | Transportation Management System |
| **YMS** | Yard Management System |
| **OMS** | Order Management System |
| **S&OP** | Sales & Operations Planning |
| **IBP** | Integrated Business Planning |
| **Safety stock** | Buffer inventory |
| **Lead time** | Time from order to delivery |
| **Bullwhip effect** | Demand variability amplification up supply chain |
| **Incoterms** | International shipping terms (FOB, CIF, etc.) |
| **FOB** | Free On Board |
| **CIF** | Cost, Insurance, Freight |
| **HS Code** | Harmonized System tariff classification |

---

## Quick Reference: Physical Flow

```process-flow
{
  "title": "Physical flow",
  "steps": [
    {
      "title": "Suppliers",
      "detail": "Raw materials, components, and manufacturers.",
      "emphasis": "Inbound logistics"
    },
    {
      "title": "Distribution network",
      "detail": "Ports, regional DCs, fulfillment centers, and stores.",
      "emphasis": "Outbound and last-mile"
    },
    {
      "title": "Customers",
      "detail": "B2B buyers, retailers, and consumers."
    },
    {
      "title": "Reverse logistics",
      "detail": "Returns, repairs, recycling, and disposal."
    }
  ]
}
```

```process-flow
{
  "title": "Information flow",
  "note": "Data moves alongside the physical network rather than after it.",
  "steps": [
    { "title": "Orders" },
    { "title": "Forecasts" },
    { "title": "Inventory status" },
    { "title": "Shipment visibility" },
    { "title": "POD" }
  ]
}
```

---

*Last updated: January 2025*
